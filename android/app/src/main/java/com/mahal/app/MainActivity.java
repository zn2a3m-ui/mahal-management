package com.mahal.app;

import android.app.Activity;
import android.app.AlertDialog;
import android.app.DownloadManager;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.content.IntentFilter;
import android.content.pm.PackageInfo;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.os.Environment;
import android.provider.Settings;
import android.webkit.JavascriptInterface;
import android.webkit.WebChromeClient;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.Toast;

import org.json.JSONArray;
import org.json.JSONObject;

import java.io.BufferedReader;
import java.io.ByteArrayOutputStream;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.net.HttpURLConnection;
import java.net.URL;

public class MainActivity extends Activity {
    private WebView webView;
    private long updateDownloadId = -1L;
    private Uri pendingInstallUri;
    private boolean receiverRegistered = false;

    private final BroadcastReceiver downloadReceiver = new BroadcastReceiver() {
        @Override public void onReceive(Context context, Intent intent) {
            if (!DownloadManager.ACTION_DOWNLOAD_COMPLETE.equals(intent.getAction())) return;
            long id = intent.getLongExtra(DownloadManager.EXTRA_DOWNLOAD_ID, -1L);
            if (id != updateDownloadId) return;
            DownloadManager manager = (DownloadManager) getSystemService(DOWNLOAD_SERVICE);
            DownloadManager.Query query = new DownloadManager.Query().setFilterById(id);
            try (android.database.Cursor cursor = manager.query(query)) {
                if (cursor != null && cursor.moveToFirst()) {
                    int status = cursor.getInt(cursor.getColumnIndexOrThrow(DownloadManager.COLUMN_STATUS));
                    if (status == DownloadManager.STATUS_SUCCESSFUL) {
                        pendingInstallUri = manager.getUriForDownloadedFile(id);
                        installDownloadedUpdate();
                    } else {
                        Toast.makeText(MainActivity.this, "تعذر تنزيل التحديث. حاول لاحقاً.", Toast.LENGTH_LONG).show();
                    }
                }
            }
        }
    };

    @Override public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        webView = new WebView(this);
        WebSettings settings = webView.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);
        settings.setAllowFileAccess(false);
        settings.setAllowContentAccess(false);
        settings.setAllowFileAccessFromFileURLs(false);
        settings.setAllowUniversalAccessFromFileURLs(false);
        settings.setSupportMultipleWindows(false);
        settings.setJavaScriptCanOpenWindowsAutomatically(false);
        settings.setMixedContentMode(WebSettings.MIXED_CONTENT_NEVER_ALLOW);
        webView.addJavascriptInterface(new BackupBridge(), "AndroidBackup");
        webView.setWebViewClient(new WebViewClient() {
            @Override public void onPageFinished(WebView view, String url) {
                super.onPageFinished(view, url);
                if (url != null && url.startsWith("file:///android_asset/")) installBackupHooks(view);
            }
        });
        webView.setWebChromeClient(new WebChromeClient());
        setContentView(webView);
        webView.loadUrl("file:///android_asset/index.html");

        IntentFilter filter = new IntentFilter(DownloadManager.ACTION_DOWNLOAD_COMPLETE);
        if (Build.VERSION.SDK_INT >= 33) {
            registerReceiver(downloadReceiver, filter, Context.RECEIVER_NOT_EXPORTED);
        } else {
            registerReceiver(downloadReceiver, filter);
        }
        receiverRegistered = true;
        checkForUpdates();
    }


    private void installBackupHooks(WebView view) {
        String script = "(function(){try{" +
            "if(!window.__idartiStorageHooked){var original=Storage.prototype.setItem;" +
            "Storage.prototype.setItem=function(k,v){var result=original.call(this,k,v);" +
            "if(this===localStorage&&window.AndroidBackup){var snap={};" +
            "for(var i=0;i<localStorage.length;i++){var key=localStorage.key(i);snap[key]=localStorage.getItem(key);}" +
            "AndroidBackup.saveSnapshot(JSON.stringify(snap));}return result;};" +
            "window.__idartiStorageHooked=true;}" +
            "var raw=AndroidBackup.getSnapshot();if(raw){var data=JSON.parse(raw),changed=false;" +
            "Object.keys(data).forEach(function(k){if(localStorage.getItem(k)===null){localStorage.setItem(k,data[k]);changed=true;}});" +
            "if(changed)return 'RESTORED';}}catch(e){}return 'READY';})()";
        view.evaluateJavascript(script, value -> {
            if ("\"RESTORED\"".equals(value)) view.reload();
        });
    }

    private class BackupBridge {
        @JavascriptInterface public synchronized String getSnapshot() {
            try (FileInputStream input = openFileInput("idarti-localstorage-backup.json");
                 ByteArrayOutputStream output = new ByteArrayOutputStream()) {
                byte[] buffer = new byte[4096];
                int count;
                while ((count = input.read(buffer)) != -1) output.write(buffer, 0, count);
                return output.toString("UTF-8");
            } catch (Exception ignored) {
                return "";
            }
        }

        @JavascriptInterface public synchronized void saveSnapshot(String json) {
            if (json == null || json.length() > 4 * 1024 * 1024) return;
            try (FileOutputStream output = openFileOutput("idarti-localstorage-backup.json", MODE_PRIVATE)) {
                output.write(json.getBytes(java.nio.charset.StandardCharsets.UTF_8));
                output.flush();
            } catch (Exception ignored) {
            }
        }
    }

    private void checkForUpdates() {
        new Thread(() -> {
            HttpURLConnection connection = null;
            try {
                URL url = new URL("https://api.github.com/repos/zn2a3m-ui/mahal-management/releases/latest");
                connection = (HttpURLConnection) url.openConnection();
                connection.setRequestMethod("GET");
                connection.setConnectTimeout(8000);
                connection.setReadTimeout(8000);
                connection.setRequestProperty("Accept", "application/vnd.github+json");
                connection.setRequestProperty("User-Agent", "Idarti-Almalia-Android");
                if (connection.getResponseCode() != HttpURLConnection.HTTP_OK) return;
                StringBuilder body = new StringBuilder();
                try (InputStream stream = connection.getInputStream();
                     BufferedReader reader = new BufferedReader(new InputStreamReader(stream))) {
                    String line;
                    while ((line = reader.readLine()) != null) body.append(line);
                }
                JSONObject release = new JSONObject(body.toString());
                String tag = release.optString("tag_name", "");
                JSONArray assets = release.optJSONArray("assets");
                if (tag.isEmpty() || assets == null || compareVersions(tag, BuildConfig.VERSION_NAME) <= 0) return;
                String downloadUrl = null;
                for (int i = 0; i < assets.length(); i++) {
                    JSONObject asset = assets.optJSONObject(i);
                    if (asset != null && "app-release.apk".equals(asset.optString("name"))) {
                        downloadUrl = asset.optString("browser_download_url", null);
                        break;
                    }
                }
                if (downloadUrl == null || downloadUrl.isEmpty()) return;
                final String latest = tag;
                final String apkUrl = downloadUrl;
                runOnUiThread(() -> new AlertDialog.Builder(MainActivity.this)
                    .setTitle("تحديث جديد متاح")
                    .setMessage("يتوفر إصدار أحدث من إدارتي المالية: " + latest + "\nهل تريد تنزيله وتثبيته الآن؟")
                    .setPositiveButton("تحديث الآن", (dialog, which) -> downloadUpdate(apkUrl))
                    .setNegativeButton("لاحقاً", null)
                    .show());
            } catch (Exception ignored) {
                // Update checks are optional; the app remains usable offline.
            } finally {
                if (connection != null) connection.disconnect();
            }
        }).start();
    }

    private int compareVersions(String remote, String current) {
        String[] a = remote.replaceFirst("^[vV]", "").split("\\.");
        String[] b = current.replaceFirst("^[vV]", "").split("\\.");
        for (int i = 0; i < Math.max(a.length, b.length); i++) {
            int x = i < a.length ? parseVersionPart(a[i]) : 0;
            int y = i < b.length ? parseVersionPart(b[i]) : 0;
            if (x != y) return Integer.compare(x, y);
        }
        return 0;
    }

    private int parseVersionPart(String value) {
        try { return Integer.parseInt(value.replaceAll("[^0-9].*$", "")); }
        catch (Exception ignored) { return 0; }
    }

    private void downloadUpdate(String url) {
        try {
            DownloadManager manager = (DownloadManager) getSystemService(DOWNLOAD_SERVICE);
            DownloadManager.Request request = new DownloadManager.Request(Uri.parse(url));
            request.setTitle("تحديث إدارتي المالية");
            request.setDescription("جارٍ تنزيل الإصدار الجديد");
            request.setMimeType("application/vnd.android.package-archive");
            request.setNotificationVisibility(DownloadManager.Request.VISIBILITY_VISIBLE_NOTIFY_COMPLETED);
            request.setDestinationInExternalFilesDir(this, Environment.DIRECTORY_DOWNLOADS, "idarti-update.apk");
            updateDownloadId = manager.enqueue(request);
            Toast.makeText(this, "بدأ تنزيل التحديث. سيظهر إشعار عند اكتماله.", Toast.LENGTH_LONG).show();
        } catch (Exception e) {
            Toast.makeText(this, "تعذر بدء تنزيل التحديث.", Toast.LENGTH_LONG).show();
        }
    }

    private void installDownloadedUpdate() {
        if (pendingInstallUri == null) return;
        if (Build.VERSION.SDK_INT >= 26 && !getPackageManager().canRequestPackageInstalls()) {
            Toast.makeText(this, "اسمح للتطبيق بتثبيت التحديث من هذا المصدر، ثم ارجع إلى التطبيق.", Toast.LENGTH_LONG).show();
            Intent settings = new Intent(Settings.ACTION_MANAGE_UNKNOWN_APP_SOURCES,
                Uri.parse("package:" + getPackageName()));
            startActivity(settings);
            return;
        }
        Intent install = new Intent(Intent.ACTION_VIEW);
        install.setDataAndType(pendingInstallUri, "application/vnd.android.package-archive");
        install.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);
        install.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
        startActivity(install);
        pendingInstallUri = null;
    }

    @Override protected void onResume() {
        super.onResume();
        if (pendingInstallUri != null && (Build.VERSION.SDK_INT < 26 || getPackageManager().canRequestPackageInstalls())) {
            installDownloadedUpdate();
        }
    }

    @Override protected void onDestroy() {
        if (receiverRegistered) {
            unregisterReceiver(downloadReceiver);
            receiverRegistered = false;
        }
        super.onDestroy();
    }

    @Override public void onBackPressed() {
        if (webView != null && webView.canGoBack()) webView.goBack(); else super.onBackPressed();
    }
}
