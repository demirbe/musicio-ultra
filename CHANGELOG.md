# 📝 Değişiklik Günlüğü

Tüm önemli değişiklikler bu dosyada belgelenecektir.

Format [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) standardına uygundur,
ve bu proje [Semantic Versioning](https://semver.org/spec/v2.0.0.html) kullanır.

## [1.0.0] - 2024-11-01

### 🎉 İlk Sürüm

#### ✨ Eklenenler
- AI destekli pitch shifting (Demucs v4)
- Vokal/enstrüman ayırma özelliği
- AudioSR ile kalite artırma
- Modern Gradio web arayüzü
- CUDA hızlandırma desteği
- 4 kalite modu (low, medium, high, ultra)
- Çoklu format desteği (MP3, WAV, FLAC, OGG, M4A)
- Otomatik model indirme
- Detaylı dokümantasyon
- Hızlı başlangıç kılavuzu
- Kurulum scriptleri (Windows/Linux/macOS)

#### 🎯 Özellikler
- -12 ile +12 semitone arası pitch değiştirme
- Real-time işlem durumu gösterimi
- Ses dosyası bilgilerini görüntüleme
- Sistem bilgilerini kontrol etme
- GPU/CPU otomatik algılama

#### 🛠️ Teknik
- PyTorch 2.5+ desteği
- CUDA 12.1+ uyumluluğu
- Rubberband algoritması entegrasyonu
- Modüler kod yapısı
- Kapsamlı hata yönetimi

---

## [Gelecek Sürümler]

### 🔮 Planlanıyor

#### [1.1.0] - Yakında
- [ ] Batch processing (toplu işlem)
- [ ] Özel preset'ler
- [ ] Ses önizleme (preview)
- [ ] İşlem geçmişi
- [ ] Favori ayarlar

#### [1.2.0] - Planlanıyor
- [ ] VST plugin desteği
- [ ] CLI (command-line) arayüzü
- [ ] API endpoint'leri
- [ ] Docker container
- [ ] Çoklu dil desteği

#### [2.0.0] - Uzun Vadeli
- [ ] Real-time pitch shifting
- [ ] Daha fazla AI modeli desteği
- [ ] Profesyonel mastering araçları
- [ ] Cloud processing
- [ ] Mobil uygulama

---

## 🐛 Bilinen Sorunlar

### v1.0.0
- AudioSR modeli yavaş çalışabilir (beklenen davranış)
- macOS'ta GPU desteği yok (Apple Silicon limitasyonu)
- Çok uzun dosyalarda bellek kullanımı yüksek olabilir

---

## 📌 Notlar

### Versiyon Numaralandırma
- **MAJOR** (1.x.x): Büyük değişiklikler, API değişiklikleri
- **MINOR** (x.1.x): Yeni özellikler, geriye dönük uyumlu
- **PATCH** (x.x.1): Bug fix'ler, küçük iyileştirmeler

### Kategoriler
- ✨ **Eklenenler**: Yeni özellikler
- 🔧 **Değiştirildi**: Mevcut özelliklerde değişiklikler
- 🐛 **Düzeltildi**: Bug fix'ler
- 🗑️ **Kaldırıldı**: Kaldırılan özellikler
- 🔒 **Güvenlik**: Güvenlik güncellemeleri

---

**🎵 Muzikio Ekibi**
