import time
import random
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import os
import requests
import json
from proxy_auth import proxies

class FastWkikiBot:
    def __init__(self):
        self.driver = None
        self.wait = None
        self.message_count = 0
        
    def test_proxy_with_requests(self):
        """Проверка прокси через requests"""
        try:
            print("🔍 Тестируем прокси через requests...")
            
            proxy_string = proxies["https"]
            proxy_parts = proxy_string.replace("http://", "").split("@")
            
            if len(proxy_parts) == 2:
                auth_part = proxy_parts[0]
                server_part = proxy_parts[1]
                username, password = auth_part.split(":")
                
                proxy_dict = {
                    'http': f'http://{username}:{password}@{server_part}',
                    'https': f'http://{username}:{password}@{server_part}'
                }
                
                # Тестируем прокси
                response = requests.get('https://api.ipify.org', proxies=proxy_dict, timeout=10)
                ip_address = response.text.strip()
                print(f"📍 IP через requests: {ip_address}")
                
                if ip_address != "185.102.186.90":
                    print("✅ Прокси работает через requests!")
                    return True
                else:
                    print("⚠️ Прокси не работает через requests")
                    return False
                    
        except Exception as e:
            print(f"❌ Ошибка при тестировании прокси через requests: {e}")
            return False

    def create_proxy_auth_extension(self, username, password, server):
        """Создание расширения для автоматической аутентификации прокси"""
        manifest_json = """
        {
            "version": "1.0.0",
            "manifest_version": 2,
            "name": "Chrome Proxy",
            "permissions": [
                "proxy",
                "tabs",
                "unlimitedStorage",
                "storage",
                "<all_urls>",
                "webRequest",
                "webRequestBlocking"
            ],
            "background": {
                "scripts": ["background.js"]
            },
            "minimum_chrome_version":"22.0.0"
        }
        """

        background_js = """
        var config = {
                mode: "fixed_servers",
                rules: {
                  singleProxy: {
                    scheme: "http",
                    host: "%s",
                    port: parseInt(%s)
                  },
                  bypassList: ["localhost"]
                }
              };

        chrome.proxy.settings.set({value: config, scope: "regular"}, function() {});

        function callbackFn(details) {
            return {
                authCredentials: {
                    username: "%s",
                    password: "%s"
                }
            };
        }

        chrome.webRequest.onAuthRequired.addListener(
                    callbackFn,
                    {urls: ["<all_urls>"]},
                    ['blocking']
        );
        """ % (server.split(':')[0], server.split(':')[1], username, password)

        import tempfile
        import zipfile

        plugin_dir = tempfile.mkdtemp()
        manifest_file = os.path.join(plugin_dir, 'manifest.json')
        with open(manifest_file, 'w') as f:
            f.write(manifest_json)

        background_file = os.path.join(plugin_dir, 'background.js')
        with open(background_file, 'w') as f:
            f.write(background_js)

        plugin_file = os.path.join(plugin_dir, 'proxy_auth_plugin.zip')
        with zipfile.ZipFile(plugin_file, 'w') as zp:
            zp.write(manifest_file, 'manifest.json')
            zp.write(background_file, 'background.js')

        return plugin_file

    def setup_driver_simple(self):
        """Настройка драйвера с автоматической аутентификацией прокси"""
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            
            # Временно отключаем системный прокси для запуска ChromeDriver
            import os
            old_http_proxy = os.environ.get('HTTP_PROXY', '')
            old_https_proxy = os.environ.get('HTTPS_PROXY', '')
            
            # Очищаем переменные прокси
            if 'HTTP_PROXY' in os.environ:
                del os.environ['HTTP_PROXY']
            if 'HTTPS_PROXY' in os.environ:
                del os.environ['HTTPS_PROXY']
            
            options = Options()
            
            # Базовые опции
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--no-sandbox")
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            
            # Настройка прокси с автоматической аутентификацией
            proxy_string = proxies["https"]
            print(f"🔧 Настраиваем прокси: {proxy_string}")
            
            # Извлекаем данные прокси
            proxy_parts = proxy_string.replace("http://", "").split("@")
            if len(proxy_parts) == 2:
                auth_part = proxy_parts[0]
                server_part = proxy_parts[1]
                username, password = auth_part.split(":")
                
                print(f"🔧 Прокси сервер: {server_part}")
                print(f"🔧 Пользователь: {username}")
                
                # Создаем расширение для автоматической аутентификации
                plugin_file = self.create_proxy_auth_extension(username, password, server_part)
                options.add_extension(plugin_file)
                
                # Дополнительные опции
                options.add_argument("--ignore-certificate-errors")
                options.add_argument("--ignore-ssl-errors")
                options.add_argument("--disable-web-security")
                options.add_argument("--allow-running-insecure-content")
            else:
                print("⚠️ Нестандартный формат прокси")
                options.add_argument(f"--proxy-server={proxy_string}")
            
            # Случайный user-agent
            user_agents = [
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
            ]
            options.add_argument(f"--user-agent={random.choice(user_agents)}")
            
            print("🔧 Настраиваем браузер с автоматической аутентификацией прокси...")
            
            self.driver = webdriver.Chrome(options=options)
            self.wait = WebDriverWait(self.driver, 30)
            
            # Маскировка
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            # Восстанавливаем переменные прокси
            if old_http_proxy:
                os.environ['HTTP_PROXY'] = old_http_proxy
            if old_https_proxy:
                os.environ['HTTPS_PROXY'] = old_https_proxy
            
            print("✅ Браузер успешно настроен")
            time.sleep(2.0)  # Ждем стабилизации браузера
            return True
            
        except Exception as e:
            print(f"❌ Ошибка при настройке драйвера: {e}")
            return False

    def check_ip_in_browser(self):
        """Проверка IP адреса в браузере"""
        try:
            print("🌐 Проверяем IP адрес в браузере...")
            
            # Пробуем несколько сервисов для проверки IP
            ip_services = [
                "https://api.ipify.org",
                "https://httpbin.org/ip",
                "https://icanhazip.com"
            ]
            
            for service in ip_services:
                try:
                    print(f"🔍 Проверяем через {service}...")
                    self.driver.get(service)
                    time.sleep(3.0)  # Увеличиваем время ожидания
                    
                    if "ipify" in service:
                        ip_element = self.driver.find_element(By.TAG_NAME, "pre")
                        ip_address = ip_element.text.strip()
                    elif "httpbin" in service:
                        ip_element = self.driver.find_element(By.TAG_NAME, "pre")
                        import json
                        data = json.loads(ip_element.text)
                        ip_address = data.get("origin", "").split(",")[0].strip()
                    else:
                        ip_element = self.driver.find_element(By.TAG_NAME, "body")
                        ip_address = ip_element.text.strip()
                    
                    print(f"📍 Ваш IP адрес: {ip_address}")
                    
                    # Проверяем, что IP отличается от ожидаемого прокси
                    if ip_address != "185.102.186.90":
                        print("✅ Прокси работает корректно в браузере!")
                        return True
                    else:
                        print("⚠️ Прокси может не работать - показывается ваш реальный IP")
                        return False
                        
                except Exception as e:
                    print(f"⚠️ Ошибка при проверке через {service}: {e}")
                    continue
            
            print("❌ Не удалось проверить IP ни через один сервис")
            return False
            
        except Exception as e:
            print(f"⚠️ Не удалось проверить IP: {e}")
            return False

    def open_uhmegle(self):
        try:
            print("🌐 Открываем uhmegle.com...")
            self.driver.get("https://uhmegle.com/")
            time.sleep(5.0)  # Увеличиваем время ожидания
            print(f"📄 Заголовок: {self.driver.title}")
            print(f"🔗 URL: {self.driver.current_url}")
            
            # Ждем полной загрузки страницы
            print("⏳ Ждем полной загрузки страницы...")
            time.sleep(3.0)
            
            # Переход на текстовый чат
            if "google_vignette" in self.driver.current_url:
                print("🔄 Переходим на текстовый чат...")
                self.driver.get("https://uhmegle.com/text/")
                time.sleep(5.0)  # Увеличиваем время ожидания
                print(f"✅ Новый URL: {self.driver.current_url}")
            
            return True
        except Exception as e:
            print(f"❌ Ошибка при открытии сайта: {e}")
            return False

    def find_and_click_start(self):
        try:
            print("🔍 Ищем кнопку Start...")
            
            # Ждем появления кнопки Start
            time.sleep(5.0)  # Увеличиваем время ожидания
            
            # Сначала пробуем найти любые кнопки на странице
            print("🔍 Сканируем все кнопки на странице...")
            all_buttons = self.driver.find_elements(By.TAG_NAME, "button")
            all_divs = self.driver.find_elements(By.TAG_NAME, "div")
            
            print(f"📊 Найдено элементов:")
            print(f"  - Кнопки: {len(all_buttons)}")
            print(f"  - Div: {len(all_divs)}")
            
            # Проверяем все кнопки
            for i, button in enumerate(all_buttons):
                try:
                    if button.is_displayed() and button.is_enabled():
                        button_text = button.text.strip().lower()
                        print(f"  Кнопка {i}: '{button.text}' (видимая: {button.is_displayed()})")
                        
                        # Ключевые слова для кнопки Start
                        start_keywords = ["start", "begin", "new", "next", "go", "continue"]
                        if any(keyword in button_text for keyword in start_keywords):
                            print(f"✅ Найдена кнопка Start: '{button.text}'")
                            print(f"🖱️ Нажимаем кнопку...")
                            button.click()
                            time.sleep(3)
                            return True
                except Exception as e:
                    print(f"  ❌ Ошибка с кнопкой {i}: {e}")
                    continue
            
            # Проверяем все div элементы
            for i, div in enumerate(all_divs):
                try:
                    if div.is_displayed() and div.is_enabled():
                        div_text = div.text.strip().lower()
                        if len(div_text) > 0 and len(div_text) < 20:  # Только короткие тексты
                            print(f"  Div {i}: '{div.text}' (видимый: {div.is_displayed()})")
                            
                            start_keywords = ["start", "begin", "new", "next", "go", "continue"]
                            if any(keyword in div_text for keyword in start_keywords):
                                print(f"✅ Найдена кнопка Start (div): '{div.text}'")
                                print(f"🖱️ Нажимаем div...")
                                div.click()
                                time.sleep(3)
                                return True
                except Exception as e:
                    continue
            
            # Расширенные селекторы
            selectors = [
                "//div[contains(text(), 'Start')]",
                "//button[contains(text(), 'Start')]",
                "//span[contains(text(), 'Start')]",
                "//a[contains(text(), 'Start')]",
                "//div[contains(@class, 'start')]",
                "//button[contains(@class, 'start')]",
                "//div[contains(@class, 'bottomButton') and contains(., 'Start')]",
                "//div[contains(@class, 'bottomButton') and contains(., 'New')]",
                "//div[contains(@class, 'bottomButton') and contains(., 'next')]",
                "//div[contains(@class, 'bottomButton') and contains(., 'NEXT')]",
                "//button[contains(., 'Start')]",
                "//button[contains(., 'New')]",
                "//div[contains(text(), 'Start')]",
                "//div[contains(text(), 'New')]"
            ]
            
            for selector in selectors:
                try:
                    element = self.driver.find_element(By.XPATH, selector)
                    if element.is_displayed() and element.is_enabled():
                        print(f"✅ Найдена кнопка: {selector}")
                        print("🖱️ Нажимаем кнопку Start...")
                        element.click()
                        time.sleep(3)  # Пауза после нажатия
                        return True
                except:
                    continue
            
            # Fallback: нажимаем любую кнопку
            buttons = self.driver.find_elements(By.TAG_NAME, "button")
            for button in buttons:
                if button.is_displayed() and button.is_enabled():
                    print("🖱️ Нажимаем любую доступную кнопку...")
                    button.click()
                    time.sleep(3)
                    return True
            
            print("❌ Кнопка Start не найдена")
            return False
            
        except Exception as e:
            print(f"❌ Ошибка при поиске кнопки Start: {e}")
            return False

    def wait_for_chat_connection(self):
        """Ожидание подключения к чату"""
        try:
            print("⏳ Ожидаем подключения к чату...")
            time.sleep(5.0)  # Ждем 5 секунд для подключения
            
            # Проверяем, что мы в чате
            try:
                # Ищем элементы чата
                chat_elements = [
                    "//div[contains(@class, 'inputContainer')]",
                    "//textarea",
                    "//div[contains(@class, 'sendButton')]",
                    "//div[contains(@class, 'chat')]"
                ]
                
                for element in chat_elements:
                    try:
                        self.driver.find_element(By.XPATH, element)
                        print("✅ Подключение к чату успешно!")
                        return True
                    except:
                        continue
                
                print("⚠️ Элементы чата не найдены, но продолжаем...")
                return True
                
            except Exception as e:
                print(f"⚠️ Ошибка при проверке чата: {e}")
                return True
                
        except Exception as e:
            print(f"❌ Ошибка при ожидании подключения: {e}")
            return False

    def send_message(self, message):
        try:
            print(f"📤 Отправляем сообщение: {message}")
            
            # Ищем поле ввода
            input_selectors = [
                "//div[contains(@class, 'inputContainer')]//textarea",
                "//textarea",
                "//input[@type='text']",
                "//div[contains(@class, 'input')]//input"
            ]
            
            input_box = None
            for selector in input_selectors:
                try:
                    input_box = self.wait.until(EC.element_to_be_clickable((By.XPATH, selector)))
                    break
                except:
                    continue
            
            if not input_box:
                print("❌ Поле ввода не найдено")
                return False
            
            # Очищаем поле и вводим текст
            input_box.clear()
            time.sleep(0.5)
            
            # Вводим текст по буквам
            for char in message:
                input_box.send_keys(char)
                time.sleep(0.1)  # Быстрее ввод
            
            time.sleep(0.5)
            
            # Ищем кнопку отправки
            send_selectors = [
                "//div[contains(@class, 'sendButton')]",
                "//button[contains(., 'Send')]",
                "//button[contains(., 'Отправить')]",
                "//input[@type='submit']"
            ]
            
            send_btn = None
            for selector in send_selectors:
                try:
                    send_btn = self.driver.find_element(By.XPATH, selector)
                    break
                except:
                    continue
            
            if send_btn:
                send_btn.click()
                time.sleep(1.0)
                print("✅ Сообщение отправлено")
                return True
            else:
                # Пробуем отправить через Enter
                input_box.send_keys(Keys.RETURN)
                time.sleep(1.0)
                print("✅ Сообщение отправлено через Enter")
                return True
                
        except Exception as e:
            print(f"❌ Ошибка при отправке сообщения: {e}")
            return False

    def disconnect_and_new(self):
        try:
            print("🔌 Отключаемся от собеседника...")
            
            # Сначала пробуем нажать Stop/Really/Next
            stop_selectors = [
                "//div[contains(@class, 'stop')]",
                "//div[contains(@class, 'really')]",
                "//div[contains(@class, 'next')]",
                "//div[contains(@class, 'bottomButton') and (contains(., 'Stop') or contains(., 'Really') or contains(., 'Next'))]",
                "//button[contains(., 'Stop')]",
                "//button[contains(., 'Next')]"
            ]
            
            for sel in stop_selectors:
                try:
                    btns = self.driver.find_elements(By.XPATH, sel)
                    for btn in btns:
                        if btn.is_displayed() and btn.is_enabled():
                            print(f"🖱️ Нажимаем кнопку: {btn.text}")
                            btn.click()
                            time.sleep(1.0)
                except Exception:
                    continue
            
            # Теперь ищем и жмём New
            new_selectors = [
                "//div[contains(@class, 'bottomButton') and contains(@class, 'new')]",
                "//div[@class='mainText' and contains(text(), 'New')]",
                "//button[contains(., 'New')]",
                "//div[contains(text(), 'New')]"
            ]
            
            for sel in new_selectors:
                try:
                    new_btn = self.driver.find_element(By.XPATH, sel)
                    if new_btn.is_displayed() and new_btn.is_enabled():
                        print("🆕 Нажимаем кнопку New...")
                        new_btn.click()
                        time.sleep(1.0)
                        return True
                except Exception:
                    continue
            
            print("⚠️ Кнопка New не найдена, но продолжаем...")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка при отключении: {e}")
            return False

    def process_one_user(self):
        try:
            print(f"\n👤 Обрабатываем пользователя #{self.message_count + 1}")
            
            # Случайный выбор одного из 3 сообщений
            messages = [
                "Hey love, got a SC? Add me and let's chat emily_meland",
                "Hey f20, Add me on snapchat and let's chat —- emily_meland",
                "Hi, I'm Emily. Let's go to Snapchat - emily_meland"
            ]
            message = random.choice(messages)
            
            if not self.send_message(message):
                return False
            
            time.sleep(2.0)  # Ждем отправки сообщения
            
            self.disconnect_and_new()
            self.message_count += 1
            time.sleep(2.0)  # Ждем перед следующим пользователем
            
            print(f"✅ Пользователь #{self.message_count} обработан")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка при обработке пользователя: {e}")
            return False

    def run(self, max_users=10):
        try:
            print("🚀 Запускаем бота...")
            
            # 1. Проверяем прокси через requests
            if not self.test_proxy_with_requests():
                print("⚠️ Прокси не работает через requests, но продолжаем...")
            
            # 2. Настраиваем браузер
            if not self.setup_driver_simple():
                print("❌ Не удалось настроить драйвер")
                return False
            
            # 3. Открываем сайт
            if not self.open_uhmegle():
                print("❌ Не удалось открыть сайт")
                return False
            
            # 4. Ищем и нажимаем Start
            if not self.find_and_click_start():
                print("❌ Не удалось найти кнопку Start")
                return False
            
            # 5. Ждем подключения к чату
            if not self.wait_for_chat_connection():
                print("⚠️ Не удалось дождаться подключения к чату, но продолжаем...")
            
            # 6. Начинаем обработку пользователей
            print(f"🔄 Начинаем обработку {max_users} пользователей...")
            while self.message_count < max_users:
                try:
                    if not self.process_one_user():
                        print("⚠️ Ошибка при обработке пользователя, продолжаем...")
                        time.sleep(3.0)
                        continue
                    time.sleep(1.0)
                except Exception as e:
                    print(f"❌ Критическая ошибка при обработке пользователя: {e}")
                    time.sleep(5.0)
                    continue
                
            print(f"🎉 Обработка завершена! Обработано пользователей: {self.message_count}")
            return True
            
        except Exception as e:
            print(f"❌ Критическая ошибка в работе бота: {e}")
            return False
        finally:
            try:
                self.cleanup()
            except Exception as e:
                print(f"⚠️ Ошибка при очистке: {e}")

    def cleanup(self):
        """Безопасное закрытие браузера"""
        try:
            if self.driver:
                print("🔒 Закрываем браузер...")
                try:
                    self.driver.quit()
                except Exception as e:
                    print(f"⚠️ Ошибка при закрытии драйвера: {e}")
                finally:
                    self.driver = None
                    print("✅ Браузер закрыт")
        except Exception as e:
            print(f"⚠️ Ошибка при закрытии браузера: {e}")

if __name__ == "__main__":
    bot = FastWkikiBot()
    bot.run(max_users=3)