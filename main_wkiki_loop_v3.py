import time
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import random
import os
from proxy_auth import proxies

class WkikiBotLoopV3:
    def __init__(self):
        """Бот с автоматической аутентификацией прокси для работы в цикле - версия 3"""
        self.driver = None
        self.wait = None
        self.message_count = 0
        
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
        
    def setup_driver(self):
        """Настройка драйвера с автоматической аутентификацией прокси"""
        options = uc.ChromeOptions()
        
        # Базовые опции
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--no-sandbox")
        
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
        
        # ВИДИМЫЙ РЕЖИМ - НЕ HEADLESS!
        # options.add_argument("--headless")  # ЗАКОММЕНТИРОВАНО
        
        print("🔧 Настраиваем браузер с автоматической аутентификацией прокси...")
        
        self.driver = uc.Chrome(options=options)
        self.wait = WebDriverWait(self.driver, 30)
        
        # Маскировка
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
    def open_uhmegle(self):
        """Открытие сайта с паузами"""
        try:
            print("🌐 Открываем uhmegle.com...")
            self.driver.get("https://uhmegle.com/")
            time.sleep(3)  # Пауза для загрузки
            
            print(f"📄 Заголовок: {self.driver.title}")
            print(f"🔗 URL: {self.driver.current_url}")
            
            # Переход на текстовый чат
            if "google_vignette" in self.driver.current_url:
                print("🔄 Переходим на текстовый чат...")
                self.driver.get("https://uhmegle.com/text/")
                time.sleep(3)
                print(f"✅ Новый URL: {self.driver.current_url}")
            
            return True
        except Exception as e:
            print(f"❌ Ошибка при открытии: {e}")
            return False
            
    def find_and_click_start(self):
        """Поиск и нажатие кнопки Start с паузами"""
        try:
            print("🔍 Ищем кнопку Start...")
            time.sleep(2)
            
            # Расширенные селекторы
            selectors = [
                "//div[contains(text(), 'Start')]",
                "//button[contains(text(), 'Start')]",
                "//span[contains(text(), 'Start')]",
                "//a[contains(text(), 'Start')]",
                "//div[contains(@class, 'start')]",
                "//button[contains(@class, 'start')]"
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
            print(f"❌ Ошибка при поиске кнопки: {e}")
            return False
            
    def wait_for_chat_interface(self, timeout=60):
        """Ожидание интерфейса чата с подробным выводом - УМЕНЬШЕНО В 2 РАЗА"""
        try:
            print("⏳ Ожидаем появления интерфейса чата...")
            time.sleep(4)  # УМЕНЬШЕНО В 2 РАЗА: было 8, стало 4
            
            # Расширенный список селекторов
            input_selectors = [
                "textarea",
                "input[type='text']",
                "input[placeholder*='message']",
                "input[placeholder*='type']",
                "input[placeholder*='chat']",
                "input[placeholder*='write']",
                ".chat-input",
                "#message-input",
                "#chat-input",
                ".message-input",
                "[contenteditable='true']",
                "input[type='textarea']",
                "div[contenteditable='true']",
                "div[role='textbox']",
                "input[class*='input']",
                "textarea[class*='input']",
                "input[class*='message']",
                "textarea[class*='message']",
                "input[class*='chat']",
                "textarea[class*='chat']"
            ]
            
            print("🔍 Ищем поле ввода...")
            for i, selector in enumerate(input_selectors, 1):
                try:
                    print(f"  {i}. Проверяем: {selector}")
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        if element.is_displayed():
                            print(f"✅ Найдено поле ввода: {selector}")
                            print(f"📝 Тип элемента: {element.tag_name}")
                            print(f"📍 Размер: {element.size}")
                            print(f"📍 Видимость: {element.is_displayed()}")
                            return element
                except Exception as e:
                    print(f"  ❌ Ошибка с {selector}: {e}")
                    continue
            
            # Попробуем найти по XPath
            print("🔍 Ищем по XPath...")
            xpath_selectors = [
                "//textarea",
                "//input[@type='text']",
                "//div[@contenteditable='true']",
                "//input[contains(@placeholder, 'message')]",
                "//input[contains(@placeholder, 'type')]",
                "//textarea[contains(@placeholder, 'message')]",
                "//textarea[contains(@placeholder, 'type')]"
            ]
            
            for i, xpath in enumerate(xpath_selectors, 1):
                try:
                    print(f"  {i}. XPath: {xpath}")
                    elements = self.driver.find_elements(By.XPATH, xpath)
                    for element in elements:
                        if element.is_displayed():
                            print(f"✅ Найдено поле ввода (XPath): {xpath}")
                            print(f"📝 Тип элемента: {element.tag_name}")
                            return element
                except Exception as e:
                    print(f"  ❌ Ошибка с XPath {xpath}: {e}")
                    continue
            
            # Последняя попытка: все элементы
            print("🔍 Ищем все элементы на странице...")
            all_inputs = self.driver.find_elements(By.TAG_NAME, "input")
            all_textareas = self.driver.find_elements(By.TAG_NAME, "textarea")
            all_divs = self.driver.find_elements(By.TAG_NAME, "div")
            
            print(f"📊 Найдено элементов:")
            print(f"  - Input: {len(all_inputs)}")
            print(f"  - Textarea: {len(all_textareas)}")
            print(f"  - Div: {len(all_divs)}")
            
            # Проверяем все input
            for i, inp in enumerate(all_inputs):
                try:
                    if inp.is_displayed():
                        print(f"  Input {i}: type={inp.get_attribute('type')}, placeholder={inp.get_attribute('placeholder')}")
                except:
                    continue
            
            # Проверяем все textarea
            for i, ta in enumerate(all_textareas):
                try:
                    if ta.is_displayed():
                        print(f"  Textarea {i}: placeholder={ta.get_attribute('placeholder')}")
                except:
                    continue
            
            print("❌ Поле ввода не найдено")
            return None
            
        except Exception as e:
            print(f"❌ Ошибка при ожидании чата: {e}")
            return None
            
    def send_message_with_delay(self, message):
        """Отправка сообщения с задержкой ввода на протяжении 2 секунд"""
        try:
            print(f"💬 Отправляем сообщение: '{message}'")
            print("⏳ Ждем 0.5 секунды перед отправкой...")  # УМЕНЬШЕНО В 2 РАЗА
            time.sleep(0.5)  # УМЕНЬШЕНО В 2 РАЗА: было 1, стало 0.5
            
            input_box = self.wait_for_chat_interface()
            if not input_box:
                print("❌ Поле ввода не найдено")
                return False
            
            print("⏳ Начинаем ввод сообщения на протяжении 2 секунд...")
            
            # Разбиваем сообщение на символы для медленного ввода
            chars = list(message)
            chars_per_second = len(chars) / 2  # Распределяем символы на 2 секунды
            
            current_text = ""
            for i, char in enumerate(chars):
                current_text += char
                input_box.clear()
                input_box.send_keys(current_text)
                
                # Пауза между символами
                if i < len(chars) - 1:  # Не делаем паузу после последнего символа
                    time.sleep(1 / chars_per_second)
            
            print("✅ Сообщение введено, отправляем...")
            time.sleep(0.5)
            input_box.send_keys(Keys.ENTER)
            
            print("✅ Сообщение отправлено!")
            time.sleep(0.5)  # УМЕНЬШЕНО В 2 РАЗА: было 1, стало 0.5
            return True
            
        except Exception as e:
            print(f"❌ Ошибка при отправке: {e}")
            return False
    
    def find_and_click_next(self):
        """Поиск и нажатие кнопки Next для поиска следующего пользователя"""
        try:
            print("🔍 Ищем кнопку для отключения/перехода к следующему...")
            time.sleep(2)  # Увеличиваем паузу для загрузки интерфейса
            
            # Сначала пробуем найти кнопки в bottomBar
            print("🔍 Ищем кнопки в bottomBar...")
            try:
                bottom_bar = self.driver.find_element(By.CLASS_NAME, "bottomBar")
                if bottom_bar.is_displayed():
                    print("✅ Найден bottomBar, ищем кнопки внутри...")
                    
                    # Ищем все кнопки в bottomBar
                    buttons_in_bar = bottom_bar.find_elements(By.TAG_NAME, "div")
                    for button in buttons_in_bar:
                        try:
                            if button.is_displayed() and button.is_enabled():
                                button_text = button.text.strip().lower()
                                print(f"  Кнопка в bottomBar: '{button.text}'")
                                
                                # Проверяем на ключевые слова
                                if any(keyword in button_text for keyword in ["stop", "really", "disconnect", "next", "skip"]):
                                    print(f"✅ Найдена кнопка отключения в bottomBar: '{button.text}'")
                                    print(f"🖱️ Нажимаем кнопку...")
                                    button.click()
                                    time.sleep(1)

                                    # После нажатия Stop пробуем подтвердить через Really?
                                    if self._click_really_confirmation():
                                        return True

                                    # Если подтверждения нет, возвращаем True, считая, что отключение прошло
                                    return True
                                     
                                 except Exception as e:
                                     continue
            except Exception as e:
                print(f"❌ Ошибка при поиске в bottomBar: {e}")
            
            # Сначала пробуем найти все кнопки на странице
            print("🔍 Сканируем все кнопки на странице...")
            all_buttons = self.driver.find_elements(By.TAG_NAME, "button")
            all_divs = self.driver.find_elements(By.TAG_NAME, "div")
            all_spans = self.driver.find_elements(By.TAG_NAME, "span")
            all_links = self.driver.find_elements(By.TAG_NAME, "a")
            
            print(f"📊 Найдено элементов:")
            print(f"  - Кнопки: {len(all_buttons)}")
            print(f"  - Div: {len(all_divs)}")
            print(f"  - Span: {len(all_spans)}")
            print(f"  - Ссылки: {len(all_links)}")
            
            # Проверяем все кнопки
            for i, button in enumerate(all_buttons):
                try:
                    if button.is_displayed() and button.is_enabled():
                        button_text = button.text.strip().lower()
                        print(f"  Кнопка {i}: '{button.text}' (видимая: {button.is_displayed()})")
                        
                        # Ключевые слова для отключения
                        disconnect_keywords = ["stop", "disconnect", "next", "skip", "end", "leave", "finish", "close", "quit", "really", "really?", "new"]
                        if any(keyword in button_text for keyword in disconnect_keywords):
                            print(f"✅ Найдена кнопка отключения: '{button.text}'")
                            print(f"🖱️ Нажимаем кнопку...")
                            button.click()
                            time.sleep(1.5)

                            # Пробуем сразу подтвердить отключение, если требуется
                            self._click_really_confirmation()

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
                            
                            disconnect_keywords = ["stop", "disconnect", "next", "skip", "end", "leave", "finish", "close", "quit", "really", "really?", "new"]
                            if any(keyword in div_text for keyword in disconnect_keywords):
                                print(f"✅ Найдена кнопка отключения (div): '{div.text}'")
                                print(f"🖱️ Нажимаем div...")
                                div.click()
                                time.sleep(1.5)

                                self._click_really_confirmation()

                                return True
                except Exception as e:
                    continue
            
            # Проверяем все span элементы
            for i, span in enumerate(all_spans):
                try:
                    if span.is_displayed() and span.is_enabled():
                        span_text = span.text.strip().lower()
                        if len(span_text) > 0 and len(span_text) < 20:
                            print(f"  Span {i}: '{span.text}' (видимый: {span.is_displayed()})")
                            
                            disconnect_keywords = ["stop", "disconnect", "next", "skip", "end", "leave", "finish", "close", "quit", "really", "really?", "new"]
                            if any(keyword in span_text for keyword in disconnect_keywords):
                                print(f"✅ Найдена кнопка отключения (span): '{span.text}'")
                                print(f"🖱️ Нажимаем span...")
                                span.click()
                                time.sleep(1.5)

                                self._click_really_confirmation()

                                return True
                except Exception as e:
                    continue
            
            # Расширенные XPath селекторы
            print("🔍 Пробуем XPath селекторы...")
            xpath_selectors = [
                "//*[contains(text(), 'STOP')]",
                "//*[contains(text(), 'Stop')]",
                "//*[contains(text(), 'stop')]",
                "//*[contains(text(), 'DISCONNECT')]",
                "//*[contains(text(), 'Disconnect')]",
                "//*[contains(text(), 'disconnect')]",
                "//*[contains(text(), 'NEXT')]",
                "//*[contains(text(), 'Next')]",
                "//*[contains(text(), 'next')]",
                "//*[contains(text(), 'SKIP')]",
                "//*[contains(text(), 'Skip')]",
                "//*[contains(text(), 'skip')]",
                "//*[contains(text(), 'END')]",
                "//*[contains(text(), 'End')]",
                "//*[contains(text(), 'end')]",
                "//*[contains(text(), 'LEAVE')]",
                "//*[contains(text(), 'Leave')]",
                "//*[contains(text(), 'leave')]",
                "//*[contains(text(), 'FINISH')]",
                "//*[contains(text(), 'Finish')]",
                "//*[contains(text(), 'finish')]",
                "//*[contains(text(), 'CLOSE')]",
                "//*[contains(text(), 'Close')]",
                "//*[contains(text(), 'close')]",
                "//*[contains(text(), 'QUIT')]",
                "//*[contains(text(), 'Quit')]",
                "//*[contains(text(), 'quit')]",
                "//*[contains(text(), 'REALLY')]",
                "//*[contains(text(), 'Really')]",
                "//*[contains(text(), 'really')]",
                "//*[contains(text(), 'REALLY?')]",
                "//*[contains(text(), 'Really?')]",
                "//*[contains(text(), 'really?')]",
                "//*[contains(text(), 'NEW')]",
                "//*[contains(text(), 'New')]",
                "//*[contains(text(), 'new')]",
                "//div[@class='mainText' and contains(text(), 'New')]",
                # Специальные селекторы для кнопки Really? на основе HTML структуры
                "//div[contains(@class, 'really')]",
                "//div[contains(@class, 'bottomButton') and contains(@class, 'really')]",
                "//div[@class='bottomButton outlined skipButton noSelect really']",
                "//div[contains(@class, 'mainText') and text()='Really?']",
                "//div[contains(@class, 'mainText') and contains(text(), 'Really')]",
                "//div[@class='bottomBar']//div[contains(@class, 'really')]",
                "//div[@class='bottomBar']//div[contains(@class, 'mainText') and text()='Really?']",
                "//div[@class='bottomBar']//div[contains(@class, 'bottomButton') and contains(@class, 'really')]",
                # Специальные селекторы для кнопки Stop на основе HTML структуры
                "//div[contains(@class, 'stop')]",
                "//div[contains(@class, 'bottomButton') and contains(@class, 'stop')]",
                "//div[@class='bottomButton outlined skipButton noSelect stop']",
                "//div[contains(@class, 'mainText') and text()='Stop']",
                "//div[contains(@class, 'mainText') and contains(text(), 'Stop')]",
                "//div[@class='bottomBar']//div[contains(@class, 'stop')]",
                "//div[@class='bottomBar']//div[contains(@class, 'mainText') and text()='Stop']",
                "//div[@class='bottomBar']//div[contains(@class, 'bottomButton') and contains(@class, 'stop')]"
            ]
            
            for selector in xpath_selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    for element in elements:
                        if element.is_displayed() and element.is_enabled():
                            print(f"✅ Найдена кнопка отключения (XPath): '{element.text}'")
                            print(f"🖱️ Нажимаем элемент...")
                            element.click()
                            time.sleep(1.5)

                            self._click_really_confirmation()

                            return True
                except Exception as e:
                    continue
            
            # Агрессивные методы отключения
            print("🔍 Пробуем агрессивные методы отключения...")
            
            # 1. Пробуем CSS селекторы для кнопок
            print("🔍 Пробуем CSS селекторы...")
            css_selectors = [
                ".bottomButton",
                ".bottomButton.stop",
                ".bottomButton.really",
                ".bottomButton.outlined",
                ".bottomButton.skipButton",
                "div[class*='stop']",
                "div[class*='really']",
                "div[class*='bottomButton']",
                ".mainText"
            ]
            
            for selector in css_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        if element.is_displayed() and element.is_enabled():
                            element_text = element.text.strip().lower()
                            print(f"  CSS элемент '{selector}': '{element.text}'")
                            
                            if any(keyword in element_text for keyword in ["stop", "really", "disconnect", "next", "skip"]):
                                print(f"✅ Найдена кнопка отключения (CSS): '{element.text}'")
                                print(f"🖱️ Нажимаем элемент...")
                                element.click()
                                time.sleep(1.5)

                                self._click_really_confirmation()

                                return True
                except Exception as e:
                    continue
            
            # 2. Пробуем нажать Escape несколько раз
            from selenium.webdriver.common.action_chains import ActionChains
            actions = ActionChains(self.driver)
            for i in range(3):
                print(f"  Попытка {i+1}: Нажимаем Escape...")
                actions.send_keys(Keys.ESCAPE).perform()
                time.sleep(1)
            
            # 3. Пробуем нажать Enter
            print("  Нажимаем Enter...")
            actions.send_keys(Keys.ENTER).perform()
            time.sleep(1.5)
            
            # 4. Пробуем нажать Tab для переключения фокуса
            print("  Нажимаем Tab...")
            actions.send_keys(Keys.TAB).perform()
            time.sleep(0.5)
            actions.send_keys(Keys.ENTER).perform()
            time.sleep(1.5)
            
            # 5. Пробуем обновить страницу
            print("  Обновляем страницу...")
            self.driver.refresh()
            time.sleep(2.5)
            
            print("✅ Агрессивные методы отключения выполнены")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка при поиске кнопки отключения: {e}")
            return False
    
    def process_one_user(self):
        """Обработка одного пользователя - отправка сообщения и переход к следующему"""
        try:
            print(f"\n👤 ОБРАБОТКА ПОЛЬЗОВАТЕЛЯ #{self.message_count + 1}")
            print("=" * 50)
            
            # Отправляем одно сообщение
            message = "Hey love, got a SC? Add me and let’s chat emily_meland"
            
            print(f"📤 ОТПРАВЛЯЕМ СООБЩЕНИЕ: '{message}'")
            
            if not self.send_message_with_delay(message):
                print("❌ Не удалось отправить сообщение")
                return False
            
            print("✅ Сообщение отправлено успешно!")
            # СРАЗУ отключаемся, без ожидания!
            print("🔌 Сразу пытаемся отключиться от текущего пользователя...")
            disconnect_attempts = 0
            max_attempts = 8  # Увеличиваем количество попыток
            
            while disconnect_attempts < max_attempts:
                disconnect_attempts += 1
                print(f"🔄 Попытка отключения #{disconnect_attempts}/{max_attempts}")
                
                if self.find_and_click_next():
                    print("✅ Отключение успешно!")
                    break
                else:
                    print(f"❌ Попытка {disconnect_attempts} не удалась")
                    time.sleep(1)  # Увеличиваем паузу между попытками
                    
                    # Дополнительные методы отключения
                    if disconnect_attempts >= 4:
                        print("🔧 Пробуем дополнительные методы отключения...")
                        try:
                            from selenium.webdriver.common.action_chains import ActionChains
                            actions = ActionChains(self.driver)
                            
                            # Пробуем разные комбинации клавиш
                            print("  Нажимаем Ctrl+W...")
                            actions.key_down(Keys.CONTROL).send_keys('w').key_up(Keys.CONTROL).perform()
                            time.sleep(1)
                            
                            print("  Нажимаем F5...")
                            actions.send_keys(Keys.F5).perform()
                            time.sleep(1.5)
                            
                            print("  Нажимаем Ctrl+R...")
                            actions.key_down(Keys.CONTROL).send_keys('r').key_up(Keys.CONTROL).perform()
                            time.sleep(1.5)
                            
                            # Пробуем найти кнопки по JavaScript
                            print("  Пробуем JavaScript поиск кнопок...")
                            js_script = """
                            var buttons = document.querySelectorAll('.bottomButton, div[class*="stop"], div[class*="really"]');
                            for(var i = 0; i < buttons.length; i++) {
                                if(buttons[i].textContent.toLowerCase().includes('stop') || 
                                   buttons[i].textContent.toLowerCase().includes('really')) {
                                    buttons[i].click();
                                    return true;
                                }
                            }
                            return false;
                            """
                            result = self.driver.execute_script(js_script)
                            if result:
                                print("✅ Кнопка найдена и нажата через JavaScript!")
                                time.sleep(2)
                                break
                            
                        except Exception as e:
                            print(f"⚠️ Ошибка при дополнительных методах: {e}")
            
            # Если все попытки не удались, принудительно обновляем страницу
            if disconnect_attempts >= max_attempts:
                print("⚠️ Все попытки отключения не удались, обновляем страницу...")
                self.driver.refresh()
                time.sleep(3)
            
            self.message_count += 1
            print(f"✅ Пользователь #{self.message_count} обработан!")
            
            # После отключения нажимаем Start для поиска нового пользователя
            print("🔄 После отключения нажимаем Start для поиска нового пользователя...")
            if not self.find_and_click_start():
                print("❌ Не удалось найти кнопку Start после отключения")
                return False
            
            # Дополнительная пауза перед поиском следующего пользователя
            print("⏳ Пауза 1.5 секунды перед поиском следующего пользователя...")
            time.sleep(1.5)
            
            return True
            
        except Exception as e:
            print(f"❌ Ошибка при обработке пользователя: {e}")
            return False
            
    def run(self, max_users=10):
        """Основной цикл с обработкой нескольких пользователей"""
        try:
            print("🚀 Запускаем Wkiki бота V3 в цикле...")
            print("🌐 Используем прокси с автоматической аутентификацией")
            print(f"⏱️ Будем обрабатывать до {max_users} пользователей")
            print("⚡ ВЕРСИЯ 3: Улучшенный поиск кнопок отключения!")
            print("=" * 50)
            
            self.setup_driver()
            if not self.open_uhmegle():
                return False
            
            print("⏳ Пауза 0.5 секунды...")  # УМЕНЬШЕНО В 2 РАЗА
            time.sleep(0.5)  # УМЕНЬШЕНО В 2 РАЗА: было 1, стало 0.5
            
            if not self.find_and_click_start():
                return False
            
            print("⏳ Пауза 1.5 секунды после нажатия Start...")  # УМЕНЬШЕНО В 2 РАЗА
            time.sleep(1.5)  # УМЕНЬШЕНО В 2 РАЗА: было 3, стало 1.5
            
            # Основной цикл обработки пользователей
            while self.message_count < max_users:
                try:
                    if not self.process_one_user():
                        print("❌ Ошибка при обработке пользователя, пробуем продолжить...")
                        time.sleep(5)  # УМЕНЬШЕНО В 2 РАЗА: было 10, стало 5
                        continue
                    
                    print(f"📊 Прогресс: {self.message_count}/{max_users} пользователей обработано")
                    
                    # Пауза между пользователями
                    print("⏳ Пауза 0.5 секунды перед следующим пользователем...")  # УМЕНЬШЕНО В 2 РАЗА
                    time.sleep(0.5)  # УМЕНЬШЕНО В 2 РАЗА: было 1, стало 0.5
                    
                except KeyboardInterrupt:
                    print("\n⏹️ Пользователь остановил бота")
                    break
                except Exception as e:
                    print(f"❌ Ошибка в цикле: {e}")
                    time.sleep(5)  # УМЕНЬШЕНО В 2 РАЗА: было 10, стало 5
                    continue
            
            print(f"🎉 Обработка завершена! Обработано пользователей: {self.message_count}")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка в работе бота: {e}")
            return False
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Безопасное закрытие браузера"""
        try:
            if self.driver:
                print("🔒 Закрываем браузер...")
                self.driver.quit()
                self.driver = None
        except Exception as e:
            print(f"⚠️ Ошибка при закрытии браузера: {e}")

    def _click_really_confirmation(self, wait_time: float = 2.0) -> bool:
        """Пробует найти и нажать кнопку подтверждения Really? после нажатия Stop."""
        try:
            time.sleep(0.5)  # даём интерфейсу обновиться
            confirm_selectors = [
                "//div[contains(@class, 'really')]",
                "//div[contains(@class, 'bottomButton') and contains(@class, 'really')]",
                "//div[@class='bottomButton outlined skipButton noSelect really']",
                "//div[contains(@class, 'mainText') and contains(text(), 'Really')]",
            ]
            for sel in confirm_selectors:
                elements = self.driver.find_elements(By.XPATH, sel)
                for el in elements:
                    try:
                        if el.is_displayed() and el.is_enabled():
                            print(f"✅ Найдена кнопка подтверждения (selector={sel}): '{el.text}'")
                            el.click()
                            time.sleep(wait_time)
                            return True
                    except Exception:
                        continue
        except Exception as e:
            print(f"⚠️ Ошибка при поиске кнопки Really?: {e}")
        return False

def main():
    """Основная функция"""
    bot = WkikiBotLoopV3()
    try:
        # Можно изменить количество пользователей (по умолчанию 10)
        success = bot.run(max_users=3)
        if success:
            print("🎉 Бот V3 завершил работу успешно!")
        else:
            print("❌ Бот V3 завершил работу с ошибками")
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
    finally:
        bot.cleanup()

if __name__ == "__main__":
    main() 