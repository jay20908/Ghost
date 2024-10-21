import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext, simpledialog
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import json
import threading
import time
import os
from bs4 import BeautifulSoup
from groq import Groq
import configparser
import logging
import pickle

class SmartWebScraperTool:
    def __init__(self, master):
        self.master = master
        self.master.title("Smart Web Scraper Tool with LLM Integration")
        self.master.geometry("1400x900")

        self.create_widgets()

        self.driver = None
        self.selected_elements = {}
        self.is_selecting = False
        self.local_storage_path = "scraped_data"
        os.makedirs(self.local_storage_path, exist_ok=True)

        self.setup_logging()
        self.load_api_key()
        self.llm_cache = {}
        self.load_cache()

    def setup_logging(self):
        logging.basicConfig(
            filename='scraper.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )

    def load_api_key(self):
        config = configparser.ConfigParser()
        config.read('config.ini')
        if 'API' in config and 'key' in config['API']:
            self.api_key = config['API']['key']
        else:
            self.api_key = simpledialog.askstring("API Key", "Enter your Groq API Key:")
            config['API'] = {'key': self.api_key}
            with open('config.ini', 'w') as configfile:
                config.write(configfile)
        self.client = Groq(api_key=self.api_key)

    def create_widgets(self):
        # Main frame
        main_frame = ttk.Frame(self.master)
        main_frame.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)

        # URL input
        url_frame = ttk.Frame(main_frame)
        url_frame.pack(pady=10, fill=tk.X)

        ttk.Label(url_frame, text="URLs (one per line):").pack(side=tk.LEFT)
        self.url_entry = scrolledtext.ScrolledText(url_frame, height=5)
        self.url_entry.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(5, 5))
        ttk.Button(url_frame, text="Load Pages", command=self.load_pages).pack(side=tk.LEFT)

        # Query input
        query_frame = ttk.Frame(main_frame)
        query_frame.pack(pady=5, fill=tk.X)

        ttk.Label(query_frame, text="Natural Language Query:").pack(side=tk.LEFT)
        self.query_entry = ttk.Entry(query_frame, width=100)
        self.query_entry.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(5, 5))
        ttk.Button(query_frame, text="Run Query", command=self.run_query).pack(side=tk.LEFT)

        # Notebook for different views
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(expand=True, fill=tk.BOTH, pady=10)

        # Elements view
        elements_frame = ttk.Frame(self.notebook)
        self.notebook.add(elements_frame, text="Elements")

        # Paned window for elements list and details
        paned_window = ttk.PanedWindow(elements_frame, orient=tk.HORIZONTAL)
        paned_window.pack(expand=True, fill=tk.BOTH)

        # Left frame for elements list
        left_frame = ttk.Frame(paned_window)
        paned_window.add(left_frame, weight=1)

        # Elements list
        self.elements_list = ttk.Treeview(left_frame, columns=("url", "tag", "text"), show="headings")
        self.elements_list.heading("url", text="URL")
        self.elements_list.heading("tag", text="Tag")
        self.elements_list.heading("text", text="Text")
        self.elements_list.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)
        self.elements_list.bind("<<TreeviewSelect>>", self.on_element_select)

        # Scrollbar for elements list
        scrollbar = ttk.Scrollbar(left_frame, orient=tk.VERTICAL, command=self.elements_list.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.elements_list.config(yscrollcommand=scrollbar.set)

        # Right frame for element details
        right_frame = ttk.Frame(paned_window)
        paned_window.add(right_frame, weight=1)

        # Element details
        self.element_details = scrolledtext.ScrolledText(right_frame, wrap=tk.WORD, width=50, height=10)
        self.element_details.pack(expand=True, fill=tk.BOTH)

        # Consistency view
        consistency_frame = ttk.Frame(self.notebook)
        self.notebook.add(consistency_frame, text="Consistency Check")

        self.consistency_text = scrolledtext.ScrolledText(consistency_frame, wrap=tk.WORD)
        self.consistency_text.pack(expand=True, fill=tk.BOTH)

        # Code blocks view
        codeblocks_frame = ttk.Frame(self.notebook)
        self.notebook.add(codeblocks_frame, text="Code Blocks")

        self.codeblocks_text = scrolledtext.ScrolledText(codeblocks_frame, wrap=tk.WORD)
        self.codeblocks_text.pack(expand=True, fill=tk.BOTH)

        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=10)

        self.select_button = ttk.Button(button_frame, text="Start Selecting", command=self.toggle_selecting)
        self.select_button.pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Remove Selected", command=self.remove_element).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Clear All", command=self.clear_elements).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Save Data", command=self.save_data).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Load Data", command=self.load_data).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Check Consistency", command=self.check_consistency).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Save Cache", command=self.save_cache).pack(side=tk.LEFT, padx=5)

        # Status bar
        self.status_var = tk.StringVar()
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def load_pages(self):
        urls = self.url_entry.get('1.0', tk.END).strip().split('\n')
        if not urls:
            messagebox.showerror("Error", "Please enter at least one URL")
            return

        self.selected_elements.clear()
        self.elements_list.delete(*self.elements_list.get_children())
        self.codeblocks_text.delete('1.0', tk.END)
        self.element_details.delete('1.0', tk.END)
        self.consistency_text.delete('1.0', tk.END)

        # Quit existing driver if any
        if self.driver:
            self.driver.quit()
            self.driver = None

        options = Options()
        # Remove headless mode to allow user interaction
        # options.add_argument('--headless')  # Comment out or remove this line
        self.driver = webdriver.Chrome(options=options)  # Ensure chromedriver is in PATH

        self.status_var.set("Loading pages...")
        self.master.update()

        # Process URLs sequentially
        for url in urls:
            self.load_and_process_page(url)

        self.status_var.set("All pages loaded")

    def load_and_process_page(self, url):
        try:
            self.driver.get(url)
            self.inject_custom_js()
            page_content = self.driver.page_source
            self.selected_elements[url] = []
            self.status_var.set(f"Loaded page: {url}")
            self.master.update()

            # Extract relevant text
            text_content = self.extract_relevant_text(page_content)
            # Process content with LLM
            llm_response = self.process_content_with_llm(text_content)
            # Update GUI with LLM response
            self.master.after(0, self.update_llm_output, url, llm_response)

        except Exception as e:
            logging.error(f"Failed to load page {url}: {str(e)}")
            self.status_var.set(f"Failed to load page: {url}")
            messagebox.showerror("Error", f"Failed to load page: {url}\nError: {str(e)}")

    def inject_custom_js(self):
        js_code = """
        function highlightElement(element) {
            element.style.outline = '2px solid red';
        }

        function unhighlightElement(element) {
            element.style.outline = '';
        }

        function selectElement(element) {
            if (element.tagName === 'BODY' || element.tagName === 'HTML') {
                return null;
            }
            var details = {
                tag: element.tagName,
                text: element.innerText,
                attributes: {},
                html: element.outerHTML
            };
            for (var i = 0; i < element.attributes.length; i++) {
                details.attributes[element.attributes[i].name] = element.attributes[i].value;
            }
            return details;
        }

        document.body.addEventListener('mouseover', function(e) {
            if (e.target.tagName !== 'BODY' && e.target.tagName !== 'HTML') {
                highlightElement(e.target);
            }
        });

        document.body.addEventListener('mouseout', function(e) {
            if (e.target.tagName !== 'BODY' && e.target.tagName !== 'HTML') {
                unhighlightElement(e.target);
            }
        });

        document.body.addEventListener('click', function(e) {
            if (e.target.tagName !== 'BODY' && e.target.tagName !== 'HTML') {
                e.preventDefault();
                window.selectedElement = selectElement(e.target);
            }
        });
        """
        self.driver.execute_script(js_code)

    def toggle_selecting(self):
        self.is_selecting = not self.is_selecting
        if self.is_selecting:
            self.select_button.config(text="Stop Selecting")
            self.start_auto_select()
        else:
            self.select_button.config(text="Start Selecting")

    def start_auto_select(self):
        def auto_select():
            while self.is_selecting:
                try:
                    selected_element = self.driver.execute_script("return window.selectedElement;")
                    if selected_element:
                        current_url = self.driver.current_url
                        self.master.after(0, self.add_element, current_url, selected_element)
                        self.driver.execute_script("window.selectedElement = null;")
                    time.sleep(0.1)  # Check every 100ms
                except Exception as e:
                    logging.error(f"Error during auto-select: {str(e)}")
                    break

        thread = threading.Thread(target=auto_select)
        thread.daemon = True
        thread.start()

    def add_element(self, url, element_data):
        if element_data:
            self.selected_elements[url].append(element_data)
            self.elements_list.insert("", "end", values=(url, element_data['tag'], element_data['text'][:30]))
            self.update_element_details(element_data)
            self.status_var.set(f"Added element from: {url}")
            self.extract_code_blocks(element_data['html'])
            logging.info(f"Element added from {url}")

    def on_element_select(self, event):
        selection = self.elements_list.selection()
        if selection:
            item = self.elements_list.item(selection[0])
            url = item['values'][0]
            index = self.elements_list.index(selection[0])
            element_data = self.selected_elements[url][index]
            self.update_element_details(element_data)

    def update_element_details(self, element_data):
        self.element_details.delete('1.0', tk.END)
        details = f"Tag: {element_data['tag']}\n\n"
        details += f"Text: {element_data['text']}\n\n"
        details += "Attributes:\n"
        for key, value in element_data['attributes'].items():
            details += f"  {key}: {value}\n"
        details += f"\nHTML:\n{element_data['html']}"
        self.element_details.insert(tk.END, details)

    def remove_element(self):
        selection = self.elements_list.selection()
        if selection:
            item = self.elements_list.item(selection[0])
            url = item['values'][0]
            index = self.elements_list.index(selection[0])
            self.elements_list.delete(selection[0])
            del self.selected_elements[url][index]
            self.element_details.delete('1.0', tk.END)
            self.status_var.set("Removed selected element")
            logging.info("Removed selected element")

    def clear_elements(self):
        self.elements_list.delete(*self.elements_list.get_children())
        self.selected_elements.clear()
        self.element_details.delete('1.0', tk.END)
        self.status_var.set("Cleared all elements")
        logging.info("Cleared all elements")

    def save_data(self):
        if not self.selected_elements:
            messagebox.showwarning("Warning", "No elements to save")
            return

        file_name = f"scrape_{int(time.time())}.json"
        file_path = os.path.join(self.local_storage_path, file_name)

        with open(file_path, 'w') as f:
            json.dump(self.selected_elements, f, indent=2)

        self.status_var.set(f"Data saved to {file_path}")
        messagebox.showinfo("Success", f"Data saved to {file_path}")
        logging.info(f"Data saved to {file_path}")

    def load_data(self):
        file_path = filedialog.askopenfilename(initialdir=self.local_storage_path,
                                               filetypes=[("JSON files", "*.json")])
        if file_path:
            with open(file_path, 'r') as f:
                loaded_data = json.load(f)

            self.clear_elements()
            for url, elements in loaded_data.items():
                self.selected_elements[url] = elements
                for element in elements:
                    self.elements_list.insert("", "end", values=(url, element['tag'], element['text'][:30]))

            self.status_var.set(f"Loaded data from {file_path}")
            logging.info(f"Loaded data from {file_path}")

    def check_consistency(self):
        self.consistency_text.delete('1.0', tk.END)

        if len(self.selected_elements) < 2:
            self.consistency_text.insert(tk.END, "Need at least two URLs to check consistency.")
            return

        urls = list(self.selected_elements.keys())
        contents = []
        for url in urls:
            elements_text = ' '.join([elem['text'] for elem in self.selected_elements[url]])
            contents.append(f"Content from {url}:\n{elements_text}")

        # Use LLM for semantic consistency check
        consistency_result = self.semantic_consistency_check(contents)
        self.consistency_text.insert(tk.END, consistency_result)
        logging.info("Consistency check completed")

    def semantic_consistency_check(self, content_list):
        prompt = "Compare the following contents for consistency:\n\n"
        for content in content_list:
            prompt += f"{content}\n\n"
        prompt += "Provide a summary of similarities and differences."

        if prompt in self.llm_cache:
            return self.llm_cache[prompt]

        try:
            response = self.client.chat.completions.create(
                model="llama3-groq-70b-8192-tool-use-preview",
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1024,
            )
            result = response.choices[0].message.content
            self.llm_cache[prompt] = result
            return result
        except Exception as e:
            logging.error(f"LLM Error during consistency check: {str(e)}")
            return "An error occurred during the consistency check."

    def extract_code_blocks(self, html):
        soup = BeautifulSoup(html, 'html.parser')
        code_blocks = soup.find_all(['pre', 'code'])

        for block in code_blocks:
            code_text = block.get_text()
            explanation = self.explain_code(code_text)
            self.codeblocks_text.insert(tk.END, f"Code Block ({block.name}):\n{code_text}\n\nExplanation:\n{explanation}\n\n")
            logging.info("Extracted and explained a code block")

    def explain_code(self, code):
        prompt = f"Explain the following code:\n\n{code}"

        if prompt in self.llm_cache:
            return self.llm_cache[prompt]

        try:
            response = self.client.chat.completions.create(
                model="llama3-groq-70b-8192-tool-use-preview",
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=512,
            )
            explanation = response.choices[0].message.content
            self.llm_cache[prompt] = explanation
            return explanation
        except Exception as e:
            logging.error(f"LLM Error during code explanation: {str(e)}")
            return "An error occurred while explaining the code."

    def run_query(self):
        query = self.query_entry.get()
        if not query:
            messagebox.showwarning("Warning", "Please enter a query")
            return

        all_contents = []
        for url in self.selected_elements:
            page_content = self.driver.page_source
            processed_content = self.extract_relevant_text(page_content)
            all_contents.append(processed_content)

        combined_content = "\n\n".join(all_contents)
        prompt = f"{query}\n\nContext:\n{combined_content}"

        if prompt in self.llm_cache:
            answer = self.llm_cache[prompt]
        else:
            try:
                response = self.client.chat.completions.create(
                    model="llama3-groq-70b-8192-tool-use-preview",
                    messages=[
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=1024,
                )
                answer = response.choices[0].message.content
                self.llm_cache[prompt] = answer
            except Exception as e:
                logging.error(f"LLM Error during query: {str(e)}")
                answer = "An error occurred while processing the query."

        messagebox.showinfo("Query Result", answer)
        logging.info("Ran a natural language query")

    def process_content_with_llm(self, content):
        prompt = f"Extract the key information from the following content:\n\n{content}"

        if prompt in self.llm_cache:
            return self.llm_cache[prompt]

        try:
            response = self.client.chat.completions.create(
                model="llama3-groq-70b-8192-tool-use-preview",
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=1024,
            )
            llm_response = response.choices[0].message.content
            self.llm_cache[prompt] = llm_response
            return llm_response
        except Exception as e:
            logging.error(f"LLM Error during content processing: {str(e)}")
            return "An error occurred while processing the content with the LLM."

    def update_llm_output(self, url, llm_response):
        # Display the LLM-processed output in the elements view
        element_data = {
            'tag': 'LLM Output',
            'text': llm_response,
            'attributes': {},
            'html': ''
        }
        self.selected_elements[url].append(element_data)
        self.elements_list.insert("", "end", values=(url, element_data['tag'], element_data['text'][:30]))
        self.update_element_details(element_data)
        logging.info(f"LLM output updated for {url}")

    def extract_relevant_text(self, html_content):
        soup = BeautifulSoup(html_content, 'html.parser')
        # Remove scripts and styles
        for script_or_style in soup(['script', 'style']):
            script_or_style.decompose()
        # Get text
        text = soup.get_text(separator='\n')
        return text

    def save_cache(self):
        with open('llm_cache.pkl', 'wb') as f:
            pickle.dump(self.llm_cache, f)
        self.status_var.set("Cache saved")
        logging.info("LLM cache saved")

    def load_cache(self):
        try:
            with open('llm_cache.pkl', 'rb') as f:
                self.llm_cache = pickle.load(f)
            logging.info("LLM cache loaded")
        except FileNotFoundError:
            self.llm_cache = {}
            logging.info("No LLM cache found, starting fresh")

    def on_closing(self):
        self.save_cache()
        if self.driver:
            self.driver.quit()
        self.master.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = SmartWebScraperTool(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()
