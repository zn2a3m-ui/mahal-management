# إدارة المحل

تطبيق عربي لإدارة **صندوق المحل والديون والجمعية**. مصدر واجهة التطبيق محفوظ مضغوطًا داخل `www/index.html.gz.b64` ويُستعاد تلقائيًا في بناء GitHub Actions.

## بناء APK
1. افتح تبويب Actions.
2. اختر آخر تشغيل **Build Android APK**.
3. نزّل artifact باسم `mahal-app-new-debug` ثم فك ضغطه وثبّت `app-debug.apk`.

## البناء محليًا
يتطلب Node.js 20 وJava 17 وAndroid SDK:
```bash
npm install
npm run restore:web
npx cap add android
npx cap sync android
cd android && ./gradlew assembleDebug
```

## ملاحظات
- معرّف التطبيق: `com.mahal.management`.
- البيانات تُحفظ محليًا على الجهاز حسب منطق التطبيق.
- هذه نسخة Debug للتجربة وليست موقعة للنشر في المتجر.
