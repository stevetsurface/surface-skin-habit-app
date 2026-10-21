# Surface app

Customer app prototype for Surface Skin Habit: booking, rebooking, package and session balance, Surface Habit points, skin analysis and doctor chat. Indonesian, mobile-first, installable as a PWA.

Live: https://stevetsurface.github.io/surface-skin-habit-app/

It looks and reads like the website ([surface-skin-habit-website](https://github.com/stevetsurface/surface-skin-habit-website)) because it is built from the same catalog and the same style tokens.

```
src/app.html          the app: styles, screens, behaviour (edit this)
build.py              reads ../website/catalog.json and ../website/assets, writes index.html
index.html            built PWA (do not hand-edit)
manifest.webmanifest, sw.js, assets/icon-*.png
```

## Build

The build expects the website repo checked out next to this one, as `../website`:

```
python3 build.py
python3 -m http.server 8766
```

Photos (clinic rooms, doctor portraits, logo) are resized from the website's assets and inlined, so `index.html` is self-contained.

## Screens

Beranda · Booking (what → clinic → doctor → date and time → confirm, then a WhatsApp confirmation) · Sesi berikutnya (rebook the package that expires first, on the date its interval suggests) · Paket & sesi · Riwayat · Struk · Rencana dokter · Setelah treatment · Analisis kulit · Chat dokter · Surface Habit · Notifikasi · Akun (pre-visit form, safety screen, notification settings, clinics, data rights).

## What is not real

Everything is demo data. The account "Ayu Lestari" is fictional, stored only in the browser. Slots, doctor replies and points are simulated. Nothing is sent anywhere; WhatsApp buttons open wa.me with a prefilled message. The photo step of the skin analysis is switched off until a licensed cosmetic-grade vendor is chosen.
