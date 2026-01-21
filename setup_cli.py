import os
import sys
import subprocess
import time
import platform
import shutil
import re

# Renk Kodları (ANSI)
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

# Windows için renk desteğini aç (Eğer gerekirse)
if os.name == 'nt':
    os.system('color')

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def get_brew_path():
    """Homebrew binary yolunu bulur (Apple Silicon veya Intel)"""
    if os.path.exists("/opt/homebrew/bin/brew"):
        return "/opt/homebrew/bin/brew"
    elif os.path.exists("/usr/local/bin/brew"):
        return "/usr/local/bin/brew"
    return None

def run_brew_command(args, capture=False):
    """Homebrew komutunu çalıştırır"""
    brew_path = get_brew_path()
    if not brew_path:
        return None

    env = os.environ.copy()
    if brew_path == "/opt/homebrew/bin/brew":
        env["PATH"] = f"/opt/homebrew/bin:{env.get('PATH', '')}"

    try:
        if capture:
            result = subprocess.run([brew_path] + args, capture_output=True, text=True, env=env)
            return result
        else:
            subprocess.check_call([brew_path] + args, env=env)
            return True
    except:
        return None

def check_homebrew():
    """Homebrew kurulu mu kontrol eder"""
    return get_brew_path() is not None

def install_homebrew():
    """Homebrew'ı kurar"""
    print(f"\n{Colors.BLUE}>> Homebrew kuruluyor...{Colors.ENDC}")
    print(f"   {Colors.WARNING}NOT: Kurulum sırasında şifreniz istenecek{Colors.ENDC}")

    try:
        install_script = '/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"'
        subprocess.call(install_script, shell=True)

        # PATH'e ekle
        brew_path = get_brew_path()
        if brew_path:
            print(f"\n{Colors.GREEN}[BAŞARILI] Homebrew kuruldu!{Colors.ENDC}")
            return True
        else:
            print(f"\n{Colors.FAIL}[HATA] Homebrew kurulumu başarısız oldu{Colors.ENDC}")
            return False
    except Exception as e:
        print(f"\n{Colors.FAIL}[HATA] Homebrew kurulumu sırasında hata: {e}{Colors.ENDC}")
        return False

def check_postgresql():
    """PostgreSQL kurulu ve çalışıyor mu kontrol eder"""
    # PostgreSQL binary kontrolü
    result = run_brew_command(["list", "postgresql@16"], capture=True)
    if not result or result.returncode != 0:
        result = run_brew_command(["list", "postgresql"], capture=True)
        if not result or result.returncode != 0:
            return False

    # PostgreSQL servis durumu
    result = run_brew_command(["services", "list"], capture=True)
    if result and "postgresql" in result.stdout:
        if "started" in result.stdout:
            return True
    return False

def install_postgresql():
    """PostgreSQL'i kurar ve başlatır"""
    print(f"\n{Colors.BLUE}>> PostgreSQL kuruluyor...{Colors.ENDC}")

    try:
        # PostgreSQL 16 kurulumu
        print("   - PostgreSQL 16 indiriliyor ve kuruluyor...")
        if not run_brew_command(["install", "postgresql@16"]):
            print(f"{Colors.FAIL}[HATA] PostgreSQL kurulumu başarısız{Colors.ENDC}")
            return False

        # Servisi başlat
        print("   - PostgreSQL servisi başlatılıyor...")
        run_brew_command(["services", "start", "postgresql@16"])

        time.sleep(3)  # Servisin başlaması için bekle

        print(f"\n{Colors.GREEN}[BAŞARILI] PostgreSQL kuruldu ve başlatıldı!{Colors.ENDC}")
        return True

    except Exception as e:
        print(f"\n{Colors.FAIL}[HATA] PostgreSQL kurulumu sırasında hata: {e}{Colors.ENDC}")
        return False

def setup_database():
    """Veritabanı ve kullanıcı oluşturur"""
    print(f"\n{Colors.BLUE}>> Veritabanı yapılandırılıyor...{Colors.ENDC}")

    try:
        # createdb komutu için PATH'e PostgreSQL ekle
        env = os.environ.copy()
        pg_bin_paths = [
            "/opt/homebrew/opt/postgresql@16/bin",
            "/usr/local/opt/postgresql@16/bin",
            "/opt/homebrew/opt/postgresql/bin",
            "/usr/local/opt/postgresql/bin"
        ]

        for pg_path in pg_bin_paths:
            if os.path.exists(pg_path):
                env["PATH"] = f"{pg_path}:{env.get('PATH', '')}"
                break

        # Kullanıcı oluştur
        print("   - PostgreSQL kullanıcısı oluşturuluyor...")
        subprocess.run(
            ["createuser", "-s", "bestwork_user"],
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        # Veritabanı oluştur
        print("   - Veritabanı oluşturuluyor...")
        result = subprocess.run(
            ["createdb", "-O", "bestwork_user", "bestwork_db"],
            env=env,
            capture_output=True,
            text=True
        )

        if result.returncode == 0 or "already exists" in result.stderr:
            print(f"{Colors.GREEN}[BAŞARILI] Veritabanı hazır!{Colors.ENDC}")
            print(f"   - Database: bestwork_db")
            print(f"   - User: bestwork_user")
            return True
        else:
            print(f"{Colors.WARNING}[UYARI] Veritabanı zaten mevcut olabilir{Colors.ENDC}")
            return True

    except Exception as e:
        print(f"{Colors.WARNING}[UYARI] Veritabanı oluşturma hatası: {e}{Colors.ENDC}")
        print(f"   Manuel olarak oluşturabilirsiniz: createdb bestwork_db")
        return False

def check_redis():
    """Redis kurulu ve çalışıyor mu kontrol eder"""
    result = run_brew_command(["list", "redis"], capture=True)
    if not result or result.returncode != 0:
        return False

    # Redis servis durumu
    result = run_brew_command(["services", "list"], capture=True)
    if result and "redis" in result.stdout:
        if "started" in result.stdout:
            return True
    return False

def install_redis():
    """Redis'i kurar ve başlatır"""
    print(f"\n{Colors.BLUE}>> Redis kuruluyor...{Colors.ENDC}")

    try:
        print("   - Redis indiriliyor ve kuruluyor...")
        if not run_brew_command(["install", "redis"]):
            print(f"{Colors.FAIL}[HATA] Redis kurulumu başarısız{Colors.ENDC}")
            return False

        print("   - Redis servisi başlatılıyor...")
        run_brew_command(["services", "start", "redis"])

        time.sleep(2)  # Servisin başlaması için bekle

        print(f"\n{Colors.GREEN}[BAŞARILI] Redis kuruldu ve başlatıldı!{Colors.ENDC}")
        return True

    except Exception as e:
        print(f"\n{Colors.FAIL}[HATA] Redis kurulumu sırasında hata: {e}{Colors.ENDC}")
        return False

def check_system_dependencies():
    """Tüm sistem bağımlılıklarını kontrol eder ve kurar"""
    print(f"\n{Colors.BOLD}=== SİSTEM BAĞIMLILIKLARI KONTROLÜ ==={Colors.ENDC}\n")

    # 1. Homebrew kontrolü
    print(f"{Colors.BLUE}[1/3] Homebrew kontrolü...{Colors.ENDC}")
    if check_homebrew():
        print(f"{Colors.GREEN}   ✓ Homebrew kurulu{Colors.ENDC}")
    else:
        print(f"{Colors.WARNING}   ✗ Homebrew bulunamadı{Colors.ENDC}")
        confirm = input(f"\n{Colors.BOLD}Homebrew kurmak ister misiniz? (e/h): {Colors.ENDC}")
        if confirm.lower() == 'e':
            if not install_homebrew():
                print(f"\n{Colors.FAIL}Homebrew olmadan devam edilemiyor. Lütfen manuel olarak kurun:{Colors.ENDC}")
                print(f"https://brew.sh/")
                return False
        else:
            print(f"{Colors.FAIL}Homebrew gerekli, kurulum iptal edildi{Colors.ENDC}")
            return False

    # 2. PostgreSQL kontrolü
    print(f"\n{Colors.BLUE}[2/3] PostgreSQL kontrolü...{Colors.ENDC}")
    if check_postgresql():
        print(f"{Colors.GREEN}   ✓ PostgreSQL kurulu ve çalışıyor{Colors.ENDC}")
    else:
        print(f"{Colors.WARNING}   ✗ PostgreSQL bulunamadı veya çalışmıyor{Colors.ENDC}")
        confirm = input(f"\n{Colors.BOLD}PostgreSQL kurmak ister misiniz? (e/h): {Colors.ENDC}")
        if confirm.lower() == 'e':
            if install_postgresql():
                setup_database()
            else:
                print(f"{Colors.WARNING}PostgreSQL kurulumu başarısız, devam ediliyor...{Colors.ENDC}")
        else:
            print(f"{Colors.WARNING}PostgreSQL kurulmadı, veritabanı işlemleri çalışmayabilir{Colors.ENDC}")

    # 3. Redis kontrolü
    print(f"\n{Colors.BLUE}[3/3] Redis kontrolü...{Colors.ENDC}")
    if check_redis():
        print(f"{Colors.GREEN}   ✓ Redis kurulu ve çalışıyor{Colors.ENDC}")
    else:
        print(f"{Colors.WARNING}   ✗ Redis bulunamadı veya çalışmıyor{Colors.ENDC}")
        confirm = input(f"\n{Colors.BOLD}Redis kurmak ister misiniz? (e/h): {Colors.ENDC}")
        if confirm.lower() == 'e':
            install_redis()
        else:
            print(f"{Colors.WARNING}Redis kurulmadı, cache özellikleri çalışmayabilir{Colors.ENDC}")

    print(f"\n{Colors.GREEN}=== SİSTEM HAZIR ==={Colors.ENDC}\n")
    return True

def print_header():
    clear_screen()
    print(f"{Colors.CYAN}")
    print("""
  ____            _   ____          __ _   
 | __ )  ___  ___| |/ ___|   ___  / _| |_ 
 |  _ \ / _ \/ __| |\___ \  / _ \| |_| __|
 | |_) |  __/\__ \ |_ ___) || (_) |  _| |_ 
 |____/ \___||___/\__|____/  \___/|_|  \__|
    """)
    print(f"{Colors.BOLD}   BESTSOFT NETWORK MARKETING SİSTEMİ - KURULUM PANELİ v26.1.5{Colors.ENDC}")
    print(f"{Colors.CYAN}" + "-" * 60 + f"{Colors.ENDC}")

    # Python Versiyon Kontrolü
    py_ver = sys.version_info
    print(f"{Colors.BLUE}>> Sistem Bilgisi: {platform.system()} {platform.release()}")
    print(f">> Python Sürümü: {py_ver.major}.{py_ver.minor}.{py_ver.micro}")
    if py_ver.major == 3 and py_ver.minor >= 12:
        print(f"{Colors.GREEN}   (Python 3.12+ uyumlu){Colors.ENDC}")
    elif py_ver.major == 3 and py_ver.minor < 10:
         print(f"{Colors.WARNING}   (UYARI: Python 3.10 veya üzeri önerilir){Colors.ENDC}")
    
    # Sanal Ortam Kontrolü
    is_venv = (sys.prefix != sys.base_prefix)
    if is_venv:
         print(f"{Colors.GREEN}>> Sanal Ortam: AKTİF (.venv){Colors.ENDC}")
    else:
         print(f"{Colors.FAIL}>> UYARI: Sanal ortam aktif değil! (Global python kullanılıyor){Colors.ENDC}")
    print(f"{Colors.CYAN}" + "-" * 60 + f"{Colors.ENDC}")

def install_requirements():
    print(f"\n{Colors.BLUE}>> Kütüphaneler yükleniyor...{Colors.ENDC}")
    try:
        # Pip upgrade
        print("   - Pip güncelleniyor...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip"], stdout=subprocess.DEVNULL)
        
        # Requirements install
        print("   - Paketler indiriliyor ve kuruluyor (requirements.txt)...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        
        print(f"\n{Colors.GREEN}[BAŞARILI] Kurulum tamamlandı.{Colors.ENDC}")
    except subprocess.CalledProcessError as e:
        print(f"\n{Colors.FAIL}[HATA] Kurulum sırasında bir sorun oluştu: {e}{Colors.ENDC}")
        print("Lütfen internet bağlantınızı kontrol edin veya yönetici olarak çalıştırın.")

def reset_db():
    print(f"\n{Colors.BLUE}>> Veritabanı işlemleri başlatılıyor...{Colors.ENDC}")
    
    if not os.path.exists("reset_db_v2.py"):
        print(f"{Colors.FAIL}[HATA] 'reset_db_v2.py' dosyası bulunamadı!{Colors.ENDC}")
        return

    try:
        print("   - Veritabanı tabloları sıfırlanıyor ve yeniden oluşturuluyor...")
        result = subprocess.run([sys.executable, "reset_db_v2.py"], capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"\n{Colors.GREEN}[BAŞARILI] Veritabanı sıfırlandı ve örnek veriler yüklendi.{Colors.ENDC}")
            print(result.stdout)
        else:
            print(f"\n{Colors.FAIL}[HATA] Veritabanı oluşturulurken hata:{Colors.ENDC}")
            print(result.stderr)
            
    except Exception as e:
        print(f"\n{Colors.FAIL}[KRİTİK HATA] {e}{Colors.ENDC}")

def update_db():
    print(f"\n{Colors.BLUE}>> Veritabanı senkronizasyonu başlatılıyor...{Colors.ENDC}")
    
    if not os.path.exists("update_db.py"):
        print(f"{Colors.FAIL}[HATA] 'update_db.py' dosyası bulunamadı!{Colors.ENDC}")
        return

    try:
        result = subprocess.run([sys.executable, "update_db.py"], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"\n{Colors.GREEN}[BAŞARILI] Veritabanı şeması güncellendi.{Colors.ENDC}")
            # print(result.stdout)
        else:
             print(f"\n{Colors.FAIL}[HATA] Güncelleme başarısız:{Colors.ENDC}")
             print(result.stderr)
    except Exception as e:
        print(f"{Colors.FAIL}[HATA] {e}{Colors.ENDC}")

def start_server():
    print(f"\n{Colors.BLUE}>> Sunucu başlatılıyor...{Colors.ENDC}")
    url = "http://127.0.0.1:8000/"
    
    print(f"   - Panel Adresi: {Colors.CYAN}{url}{Colors.ENDC}")
    print("   - Çıkış Yapmak İçin: CTRL + C")
    
    # Tarayıcıyı aç
    time.sleep(2)
    try:
        if platform.system() == "Darwin":
            subprocess.call(["open", url])
        elif platform.system() == "Windows":
            os.system(f"start {url}")
        else:
            # Linux
            subprocess.call(["xdg-open", url])
    except:
        pass # Tarayıcı açılamazsa sisteme engel olmasın
        
    # Uvicorn'u başlat
    try:
        # reload=True geliştirme ortamı için. Prodüksiyonda False olmalı ama burası kurulum paneli.
        subprocess.call([sys.executable, "-m", "uvicorn", "app.main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"])
    except KeyboardInterrupt:
        print(f"\n{Colors.WARNING}Sunucu kullanıcı tarafından durduruldu.{Colors.ENDC}")

def main():
    while True:
        print_header()
        print(f"{Colors.BOLD}İŞLEM MENÜSÜ:{Colors.ENDC}")
        print("0. [SİSTEM] Homebrew + PostgreSQL + Redis Kontrol/Kurulum")
        print("1. [HIZLI KURULUM] Kütüphaneleri Yükle + DB Sıfırla")
        print("2. [GÜNCELLEME] Kütüphaneleri Yükle + DB Senkronize Et (Veri Kaybı Olmaz)")
        print("3. [ONARIM] Sadece Veritabanını Sıfırla (DİKKAT: Veriler Silinir)")
        print("4. [BAŞLAT] Sunucuyu Çalıştır")
        print("5. Çıkış")
        print(f"{Colors.CYAN}" + "-" * 60 + f"{Colors.ENDC}")

        choice = input(f"{Colors.BOLD}Seçiminiz (0-5): {Colors.ENDC}")

        if choice == '0':
            if check_system_dependencies():
                input("\nDevam etmek için Enter'a basın...")
            else:
                input("\nHata oluştu. Enter'a basın...")
        elif choice == '1':
            install_requirements()
            reset_db()
            input("\nDevam etmek için Enter'a basın...")
        elif choice == '2':
            install_requirements()
            update_db()
            input("\nDevam etmek için Enter'a basın...")
        elif choice == '3':
            print(f"\n{Colors.FAIL}!!! DİKKAT !!!{Colors.ENDC}")
            print("Bu işlem mevcut tüm siparişleri, kullanıcıları ve ayarları silecektir.")
            confirm = input("Onaylıyor musunuz? (evet/hayir): ")
            if confirm.lower() == 'evet':
                reset_db()
            else:
                print("İşlem iptal edildi.")
            input("\nDevam etmek için Enter'a basın...")
        elif choice == '4':
            start_server()
            # Sunucu kapandıktan sonra döngüye dönmemesi için çıkabiliriz veya dönebiliriz.
            # Genelde sunucu kapandığında menüye dönmek iyidir.
            input("\nMenüye dönmek için Enter'a basın...")
        elif choice == '5':
            print("Çıkış yapılıyor...")
            sys.exit()
        else:
            input("Geçersiz seçim. Tekrar denemek için Enter'a basın...")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nÇıkış yapıldı.")
