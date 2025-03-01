import json
import subprocess
import sys
import tkinter as tk
from tkinter import Frame, Image, IntVar, messagebox, filedialog, ttk, Menu, Toplevel
from tkinter import filedialog, messagebox, scrolledtext, Frame, Checkbutton, IntVar, Entry, ttk
import os
import threading
from PIL import Image, ImageTk

from tkinter import PhotoImage
import zipfile

sort_options = ["Name", "Datum", "Größe"]
deleted_logs = {}  # Dictionary, um gelöschte Logs nach Season zu speichern
current_season = 1  
ADB_PATH = (r"platform-tools\adb.exe")
editor_window = None
text_editor = None
download_ico = None
copy_ico = None
CONFIG_FILE = "config.json" 
############# FAST SAFE ########################################################################################################################



def load_language_setting():
        # Versuche, die Sprache aus der Konfigurationsdatei zu laden
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                config = json.load(f)
                
                return config.get("language", "de")  # Standardmäßig Deutsch, wenn nichts gesetzt ist
        except (FileNotFoundError, json.JSONDecodeError):
            return "de"  # Standardmäßig Deutsch
        
def load_translations():
        # Lade alle Übersetzungen aus der JSON-Datei
        with open("translations.json", "r", encoding="utf-8") as f:
            return json.load(f)

def get_texts(language_code):
        # Übersetzungen für die ausgewählte Sprache zurückgeben
        return translations.get(language_code, translations["en"])  # Fallback auf Englisch

def update_texts():
    pass

def get_media_files(directory, selected_types, custom_extensions):
    files = []
    try:
        command = f"{ADB_PATH} shell ls -R \"{directory}\""
        process = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8', errors='replace', universal_newlines=True)

        # Die Ausgabe von stdout verarbeiten, aber nichts anzeigen
        output = process.stdout.splitlines()

        current_dir = ''

        for line in output:
            # Überprüfe, ob es ein Verzeichnisname ist oder eine Datei
            if line.endswith(':'):
                current_dir = line[:-1]
            else:
                full_path = os.path.join(current_dir, line).replace('\\', '/')
                if any(full_path.endswith(ext) for ext in selected_types) or \
                   any(full_path.endswith(ext) for ext in custom_extensions):
                    files.append(full_path)

        return files

    except Exception as e:
        # Fehler abfangen, aber keine Ausgabe anzeigen
        return []


def create_directories(base_folder):

    if sys.platform == "win32":
        import ctypes
        ctypes.windll.kernel32.SetConsoleOutputCP(65001)

    directories = {
        texts["Bilder"]: os.path.join(base_folder, texts['Backup'], texts['Bilder']),
        texts["Musik"]: os.path.join(base_folder, texts['Backup'], texts['Musik']),
        texts["Videos"]: os.path.join(base_folder, texts['Backup'], texts['Videos']),
        texts["APKS"]: os.path.join(base_folder, texts['Backup'], texts['APKS']),
        texts["Archive"]: os.path.join(base_folder, texts['Backup'], texts['Archive']),
        texts["Documente"]: os.path.join(base_folder, texts['Backup'], texts['Documente']),
        texts["Custom"]: os.path.join(base_folder, texts['Backup'], texts['Custom'])
    }
    
    for dir_name, dir_path in directories.items():
        os.makedirs(dir_path, exist_ok=True)
    
    return directories

def copy_selected_files(selected_files, directories, log_widget, progress_bar, custom_extensions):
    total_files = len(selected_files)
    for index, file in enumerate(selected_files):
        file_name = os.path.basename(file)
        if file.endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp', '.heif', '.svg', '.raw')):
            dest_folder = directories[texts["Bilder"]]
        elif file.endswith(('.mp3', '.wav', '.aac', '.flac', '.ogg', '.m4a', '.wma', '.opus', '.alac', '.aiff')):
            dest_folder = directories[texts['Musik']]
        elif file.endswith(('.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm', '.mpeg', '.mpg', '.3gp', '.m4v', '.vob', '.ts')):
            dest_folder = directories[texts['Videos']]
        elif file.endswith('.apk'):
            dest_folder = directories[texts['APKS']]
        elif file.endswith(('.zip', '.rar', '.tar', '.gz', '.bz2', '.7z', '.xz', '.z', '.tar.gz', '.tar.bz2', '.tar.xz', '.cab', '.iso', '.lz', '.lzma', '.arc', '.zstd')):
            dest_folder = directories[texts['Archive']]
        elif file.endswith(('.doc', '.docx', '.txt', '.pdf', '.ppt', '.pptx', '.xls', '.xlsx', '.odt', '.ods', '.odp', '.rtf', '.html', '.xml', '.csv', '.md', '.epub', '.mobi', '.wps', '.pages', '.xps')):
            dest_folder = directories[texts['Documente']]
        elif any(file.endswith(ext) for ext in custom_extensions):
            dest_folder = directories[texts['Custom']]
        else:
            continue
        
        command = f"{ADB_PATH} pull \"{file}\" \"{dest_folder}/\""
        log_widget.insert(tk.END, f"{texts['copyFile']}{file}\n", 'copy')
        log_widget.see(tk.END)
        
        try:
            result = subprocess.run(command, shell=True, capture_output=True, text=True)
            if result.returncode != 0:
                log_widget.insert(tk.END, f"{texts['copyError']}{file}: {result.stderr}\n", 'error')
                log_widget.see(tk.END)
            else:
                log_widget.insert(tk.END, f"{texts['copySuccess']}{file}\n", 'noerror')
                log_widget.see(tk.END)
        except Exception as e:
            log_widget.insert(tk.END, f"{texts['copyError']}{file}: {str(e)}\n", 'error')
            log_widget.see(tk.END)        

            

        


def zip_directory(directory_path, zip_name, log_widget):
    with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(directory_path):
            for file in files:
                file_path = os.path.join(root, file)
                zipf.write(file_path, os.path.relpath(file_path, os.path.dirname(directory_path)))
    log_widget.insert(tk.END, texts["createZip"].format(zip_name=zip_name), 'copy')

    log_widget.see(tk.END)
    return zip_name

def delete_directories(directories, log_widget):
    for dir_path in directories.values():
        try:
            for root, _, files in os.walk(dir_path, topdown=False):
                for file in files:
                    os.remove(os.path.join(root, file))
                os.rmdir(root)
            log_widget.insert(tk.END, f"{texts["deleteFolder"]} {dir_path}\n", 'noerror')
            log_widget.see(tk.END)
        except Exception as e:
            log_widget.insert(tk.END, f"{texts["deleteError"]} {dir_path}: {str(e)}\n", 'error')
            log_widget.see(tk.END)

def process_media(log_widget, dest_folder, selected_types, custom_extensions, zip_files, delete_files, zip_file_name, progress_bar=None):
    log_widget.insert(tk.END, f"{texts['ScanSDCARD']}\n", 'noerror')
    log_widget.see(tk.END)

    selected_files = get_media_files('/sdcard', selected_types, custom_extensions)

    if not selected_files:
        log_widget.insert(tk.END, f"{texts["noFilesFound"]}")
        log_widget.see(tk.END)
        return

    log_widget.insert(tk.END, f"{len(selected_files)} {texts['selectedFiles']}\n", 'copy')
    log_widget.see(tk.END)

    directories = create_directories(dest_folder)

    copy_selected_files(selected_files, directories, log_widget, progress_bar, custom_extensions)

    if zip_files:
        zip_file_path = os.path.join(dest_folder, zip_file_name)
        zip_directory(dest_folder, zip_file_path, log_widget)

    # Löschen der Ordner nach ZIP-Erstellung, wenn die Checkbox aktiviert ist
    if delete_files:
        delete_directories(directories, log_widget)

    log_widget.insert(tk.END, f"{len(selected_files)} {texts['filesCopied']}")########################################################
    log_widget.insert(tk.END, f"{texts['copyComplete']}", 'finsih')
    log_widget.see(tk.END)

def toggle_entry(zip_var, zip_entry):
    # Sichtbarkeit des Eingabefelds steuern
    if zip_var.get() == 1:  # Checkbox ist aktiviert
        zip_entry.pack(pady=5)  # Eingabefeld anzeigen
    else:  # Checkbox ist nicht aktiviert
        zip_entry.pack_forget()  # Eingabefeld ausblenden

def show_selection_window(log_widget, dest_folder):
    selection_window = tk.Toplevel(root)
    selection_window.title(f"{texts['settingsForSafe']}")
    selection_window.geometry("400x400")
    
    selection_window.resizable(False, False)
    checkbox_frame = Frame(selection_window)
    checkbox_frame.pack(pady=10)

    selected_types = []
    file_types = {
        f"{texts['Bilder']}": ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp', '.heif', '.svg', '.raw'],
        f"{texts['Musik']}": ['.mp3', '.wav', '.aac', '.flac', '.ogg', '.m4a', '.wma', '.opus', '.alac', '.aiff'],
        f"{texts['Videos']}": ['.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm', '.mpeg', '.mpg', '.3gp', '.m4v', '.vob', '.ts'],
        f"{texts['APKS']}": ['.apk'],
        f"{texts['Archive']}": ['.zip', '.rar', '.tar', '.gz', '.bz2', '.7z', '.xz', '.z', '.tar.gz', '.tar.bz2', '.tar.xz', '.cab', '.iso', '.lz', '.lzma', '.arc', '.zstd'],
        f"{texts['Documente']}": ['.doc', '.docx', '.txt', '.pdf', '.ppt', '.pptx', '.xls', '.xlsx', '.odt', '.ods', '.odp', '.rtf', '.html', '.xml', '.csv', '.md', '.epub', '.mobi', '.wps', '.pages', '.xps']
    }

    for type_name, extensions in file_types.items():
        var = IntVar()
        cb = Checkbutton(checkbox_frame, text=type_name, variable=var)
        cb.pack(anchor='w')
        selected_types.append((var, extensions))

    # Custom Extension Eingabe
    extension_label = tk.Label(checkbox_frame, text=texts['enterCustomExtensions'])
    extension_label.pack(anchor='w')
    custom_extension_entry = Entry(checkbox_frame)
    custom_extension_entry.pack(anchor='w')



# Eingabefeld für den ZIP-Dateinamen


    delete_files_var = tk.BooleanVar()
    delete_files_checkbox = Checkbutton(checkbox_frame, text=texts['deleteAfterZip'], variable=delete_files_var)
    delete_files_checkbox.pack()

    # ZIP-Datei Erstellung Checkbox

    zip_var = IntVar()
    zip_checkbox = Checkbutton(checkbox_frame, text=texts['createZip'], variable=zip_var, command=lambda: toggle_entry(zip_var, zip_entry))
    zip_checkbox.pack(anchor='w')

    # Eingabefeld für den ZIP-Dateinamen
    zip_entry = Entry(checkbox_frame)
    zip_entry.pack_forget()


    def process_selection():
        clear_log_temporarily(log_widget)
        custom_extensions = custom_extension_entry.get().strip()
        selected_types_list = []

        if custom_extensions:
            # Trennen der benutzerdefinierten Endungen durch Kommas
            custom_extensions_list = [ext.strip() for ext in custom_extensions.split(',')]
        else:
            custom_extensions_list = []

        for var, extensions in selected_types:
            if var.get():
                selected_types_list.extend(extensions)

        # ZIP-Erstellung basierend auf der Checkbox
        create_zip = zip_var.get()  # 1 wenn ausgewählt, 0 wenn nicht
        zip_file_name = zip_entry.get().strip()

        if not zip_file_name:
            zip_file_name = "Backup.zip"
    
    # Sicherstellen, dass die ZIP-Dateiendung vorhanden ist
        if not zip_file_name.endswith('.zip'):
            zip_file_name += '.zip'

        threading.Thread(target=process_media, args=(log_widget, dest_folder, selected_types_list, custom_extensions_list, create_zip, delete_files_var.get(), zip_file_name)).start()

        selection_window.destroy()

    process_button = tk.Button(selection_window, text=texts['confirm'], command=process_selection)
    process_button.pack(pady=10)

def start_backup(log_widget, progress_bar):
    dest_folder = filedialog.askdirectory(title=texts['chooseSafeDestinationFolder'])
    if not dest_folder:
        return

    show_selection_window(log_widget, dest_folder)


def save_log_to_file(log_widget):
    # Dateiauswahl-Dialog öffnen, damit der Benutzer den Speicherort auswählt
    file_path = filedialog.asksaveasfilename(defaultextension=".html", 
                                             filetypes=[("HTML files", "*.html"), ("All files", "*.*")],
                                             title=texts['saveLogAs'])
    if not file_path:
        return  # Falls der Benutzer den Dialog abbricht
    
    try:
        with open(file_path, "w", encoding='utf-8') as file:
            # HTML-Kopf
            file.write("<html><body>\n")
            # Alle gelöschten Season-Logs speichern
            for season, log in deleted_logs.items():
                file.write(f"<h2>{season}</h2><pre>{log}</pre><br>\n")
            
            # Aktuellen Log speichern
            file.write("<h2>Last Season</h2><pre>")
            log_content = get_colored_text(log_widget)
            file.write(log_content)
            file.write("</pre>\n")
            # HTML-Ende
            file.write("</body></html>")
    except Exception as e:
        log_widget.insert(tk.END, f"{texts['saveError']} {str(e)}\n")

def get_colored_text(log_widget):
    # Holt den Text mit Formatierungen aus dem log_widget
    text_content = ""
    # Zeilenweise durch den Text gehen
    for i in range(int(log_widget.index('end-1c').split('.')[0])):  # für jede Zeile
        line = log_widget.get(f"{i}.0", f"{i+1}.0")  # Holen Sie sich die Zeile
        # Formatierungen der Zeile abfragen
        tags = log_widget.tag_names(f"{i}.0")
        line_content = ""  # In dieser Variable wird der formatierte Text gesammelt
        # Fügen Sie die Formatierungen für die Tags hinzu
        for tag in tags:
            if tag == "error":
                line_content += f'<span style="color:red;">{line.strip()}</span>'
                break
            elif tag == "noerror":
                line_content += f'<span style="color:green;">{line.strip()}</span>'
                break
            elif tag == "finish":
                line_content += f'<span style="color:blue;">{line.strip()}</span>'
            elif tag == "copy":
                line_content += f'<span style="color:#0A5F70;">{line.strip()}</span>'
                break
            # Fügen Sie hier weitere Farben hinzu, die Sie verwenden

        if not line_content:  # Wenn keine Tags, Text einfach hinzufügen
            line_content = line.strip()
        
        text_content += line_content + "<br>"  # Fügen Sie die Zeile zum Gesamttext hinzu
    return text_content


def clear_log_temporarily(log_widget):
    global current_season
    # Speichert den aktuellen Inhalt in der temporären Season
    log_content = ""
    
    # Durch alle Zeilen im Text Widget iterieren
    for i in range(int(log_widget.index('end-1c').split('.')[0])):  # für jede Zeile
        line = log_widget.get(f"{i}.0", f"{i+1}.0")  # Holen Sie sich die Zeile
        tags = log_widget.tag_names(f"{i}.0")  # Holen Sie sich die Tags für diese Zeile
        
        # Initialisiere eine Variable für die gefärbte Zeile
        line_with_color = ""
        
        for tag in tags:
            if tag == "error":
                line_with_color = f'<span style="color:red;">{line.strip()}</span>'
                break
            elif tag == "noerror":
                line_with_color = f'<span style="color:green;">{line.strip()}</span>'
                break
            elif tag == "finish":
                line_with_color = f'<span style="color:blue;">{line.strip()}</span>'
                break
            elif tag == "copy":
                line_with_color = f'<span style="color:#0A5F70;">{line.strip()}</span>'
                break
            # Fügen Sie hier weitere Farben hinzu, die Sie verwenden

        # Nur gefärbte Zeilen hinzufügen
        if line_with_color:
            log_content += line_with_color + "<br>"  # Fügen Sie die gefärbte Zeile zum Gesamttext hinzu

    if log_content:
        season_name = f"Season {current_season}"
        deleted_logs[season_name] = log_content  # Speichert den gelöschten Log
        current_season += 1  # Erhöht die Season-Nummer für das nächste Mal
        log_widget.delete("1.0", tk.END)  # Löscht den Inhalt des Widgets
        log_widget.insert(tk.END, f"{season_name} {texts['delandSafe']}\n")



def open_fast_frame():
    top = Toplevel()  # Erstelle ein neues Toplevel-Fenster
    top.title(texts['schnellesSichern'])

    try:
        img = Image.open(r"img\explorer.ico")
        img = img.resize((50, 50))  # Ändere die Größe nach Bedarf
        icon_photo = ImageTk.PhotoImage(img)
        top.iconphoto(False, icon_photo)  # Setze das Icon für das Fenster
    except Exception as e:
        print(f"Fehler beim Laden des Icons: {e}")
    
    top.geometry("600x400")
    top.resizable(False, False)
    top.config(background="#323232")

    # Frame für das Log-Widget
    log_frame = Frame(top, bg="#323232")
    log_frame.place(relx=0.02, rely=0.05, relwidth=0.96, relheight=0.75)

    log_widget = scrolledtext.ScrolledText(log_frame)
    log_widget.config(bg="black", fg="white", wrap="word")
    log_widget.tag_config('error', foreground='red')
    log_widget.tag_config('noerror', foreground='green')
    log_widget.tag_config('finish', foreground='blue')
    log_widget.tag_config('copy', foreground='#0A5F70')
    log_widget.place(relx=0, rely=0, relwidth=1, relheight=1)

    # Fortschrittsbalken unter dem Log-Widget
    progress_bar = ttk.Progressbar(top, orient='horizontal', length=400, mode='determinate')
    progress_bar.place(relx=0.02, rely=0.82, relwidth=0.96, relheight=0.05)

    # Start-Button, platziert rechts unten
    start_button = tk.Button(top, text=texts['startBackup'], command=lambda: start_backup(log_widget, progress_bar))
    start_button.place(relx=0.72, rely=0.9, relheight=0.08, relwidth=0.25)

    # Safe Log-Button, daneben
    save_button = tk.Button(top, text=texts['safeLOG'], command=lambda: save_log_to_file(log_widget))
    save_button.place(relx=0.47, rely=0.9, relheight=0.08, relwidth=0.2)

###########################################################################################################################################



def run_adb_command(command):
    """Führt einen adb-Befehl aus und gibt die Ausgabe live in der Konsole aus."""
    try:
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8")

        output_lines = []  # Liste zur Speicherung der Ausgaben
        output_found = False  # Flag, um zu prüfen, ob eine Ausgabe gefunden wurde

        # Lies die Ausgabe Zeile für Zeile
        while True:
            output = process.stdout.readline()  # Lese die Standardausgabe
            if output == '' and process.poll() is not None:  # Prozess beendet
                break
            if output:
                output_found = True
                output_lines.append(output.strip())  # Speichere die Zeile in der Liste
                
                sys.stdout.flush()  # Sofortige Anzeige der Ausgabe

        # Fehlerausgabe prüfen
        stderr = process.stderr.read()
        process.wait()  # Warte, bis der Prozess beendet ist

        if process.returncode != 0:
            pass

        # Rückgabe der Standardausgabe als Liste von Zeilen
        return output_lines if output_found else []

    except Exception as e:
        
        return []

def list_files(directory):
    """Zeige die Dateien eines Verzeichnisses auf dem Handy an."""
    directory = directory.replace(" ", "\\ ")  # Ersetze Leerzeichen für den Shell-Befehl
    command = f'{ADB_PATH} shell ls -pa "{directory}"'

    output = run_adb_command(command)  # Führe den Befehl aus und erhalte die Ausgabe

    if not output:  # Überprüfe, ob die Ausgabe leer ist
        
        return []  # Gebe eine leere Liste zurück

    # Gib die aufgeteilte Ausgabe zurück
    return output  # Gibt die Liste der Dateien zurück




# Hier wäre die Methode, um die ausgewählten Dateien zu erhalten (diese musst du anpassen)
def on_right_click(event, selected_files_to_copy):
    show_context_menu(event, selected_files_to_copy)

def sort_files(files, criterion):
    """Sortiere die Dateien basierend auf dem gewählten Kriterium."""
    if criterion == "Name":
        return sorted(files, key=lambda x: x[0].lower())
    elif criterion == "Datum":
        return sorted(files, key=lambda x: x[1])  # Hier müsste das Datum bereitgestellt werden
    elif criterion == "Größe":
        return sorted(files, key=lambda x: x[2])  # Hier müsste die Größe bereitgestellt werden
    return files


def update_file_list(directory, sort_criterion="Name"):
    """Aktualisiere die Dateiliste mit den Dateien des ausgewählten Verzeichnisses."""
    global current_directory
    
    if not directory.endswith('/'):
        directory += '/'
    
    current_directory = directory
    list_files(directory)
    
    # Hole die Liste der Dateien und ihrer Attribute (hier als Platzhalter)
    files = list_files(directory)
    
    # Leere die Treeview und füge die neuen Dateien hinzu
    directory_tree.delete(*directory_tree.get_children())
    
    # Füge ".." hinzu, um ins vorherige Verzeichnis zu gelangen
    directory_tree.insert("", "end", text="..", image=folder_icon, values=(directory,), tags=("folder",))
    
    # Sortiere die Dateien nach dem gewählten Kriterium
    sorted_files = sort_files(files, sort_criterion)

    # Füge die sortierten Dateien hinzu
    for file in sorted_files:
        full_path = os.path.join(current_directory, file)
        
        if file.endswith('/'):
            directory_tree.insert("", "end", text=file, image=folder_icon, values=(full_path,), tags=("folder",))
        else:
            directory_tree.insert("", "end", text=file, image=file_icon, values=(full_path,), tags=("file",))
    
    update_path_display()  # Aktualisiere die Anzeige des Pfads
    

def on_treeview_double_click(event):
    """Verarbeite einen Doppelklick in der Treeview."""
    selected_item = directory_tree.selection()[0]
    selected_item_text = directory_tree.item(selected_item, "text")
    
    # Wenn '..' ausgewählt wurde, gehe zurück
    if selected_item_text == '..':
        on_back_button_click()
    else:
        selected_item_values = directory_tree.item(selected_item, "values")
        if selected_item_values:
            new_directory = selected_item_values[0]
            if not new_directory.endswith('/'):  # Verzeichnis sicherstellen
                new_directory += '/'
            update_file_list(new_directory)


def on_back_button_click():
    """Gehe ins vorherige Verzeichnis."""
    global current_directory
    if current_directory != '/':
        current_directory = os.path.dirname(current_directory.rstrip('/'))
        update_file_list(current_directory)



def on_treeview_select(event):
    selected_items = directory_tree.selection()  # Holen Sie sich alle ausgewählten Elemente
    global selected_files_to_copy  # Global verwenden, um die Liste zu aktualisieren
    selected_files_to_copy.clear()  # Leere die Liste der ausgewählten Dateien

    for item in selected_items:
        selected_item_text = directory_tree.item(item, "text")
        selected_files_to_copy.append(selected_item_text)
    
    
       

def copy_files(local_path):
    # Den Kopiervorgang in einem separaten Thread starten
    threading.Thread(target=start_copy, args=(local_path,)).start()




def start_copy(local_path):
    """Kopiere die ausgewählten Dateien oder Verzeichnisse in den Zielordner."""
    total_files = len(selected_files_to_copy)

    if total_files == 0:
        messagebox.showwarning(texts['warning'], texts['noFilesSelectedForCopy'])
        return

    for index, file in enumerate(selected_files_to_copy):
        source_path = os.path.join(current_directory, file)
        destination_path = os.path.join(local_path, file)

        # Stelle sicher, dass das Zielverzeichnis existiert
        destination_dir = os.path.dirname(destination_path)
        if not os.path.exists(destination_dir):
            os.makedirs(destination_dir)

        # Führe adb pull aus, um die Dateien zu kopieren
        command = [ADB_PATH, 'root', 'pull', source_path, destination_path]      
        command = [ADB_PATH, 'pull', source_path, destination_path]
        output = run_adb_command(command)

        # Füge hier Debugging-Ausgaben hinzu
        
        if output:  # Wenn es eine Ausgabe gibt, zeige sie an
            pass
        else:
            pass

        # Update der Fortschrittsanzeige
        progress = (index + 1) / total_files * 100  # Berechne den Fortschritt in Prozent
        progress_var.set(progress)  # Setze den Fortschritt in der Fortschrittsanzeige
        root.update_idletasks()  # Aktualisiere die GUI

    messagebox.showinfo(texts['success'], texts['fileCopiedToDevice'])
    progress_var.set(0)  # Setze den Fortschritt nach Abschluss zurück


def Start_Del_files():
    # Den Kopiervorgang in einem separaten Thread starten
    threading.Thread(target=Delete_files).start()


def Delete_files():
    """Kopiere die ausgewählten Dateien oder Verzeichnisse in den Zielordner."""
    total_files = len(selected_files_to_copy)
    

    if total_files == 0:
        messagebox.showwarning(texts['warning'], texts['noFilesSelectedForCopy'])
        return

    for index, file in enumerate(selected_files_to_copy):
        source_path = os.path.join(current_directory, file)
        
        source_path = f'"{source_path}"'
        # Stelle sicher, dass das Zielverzeichnis existiert


        # Führe adb pull aus, um die Dateien zu kopieren
        command = [ADB_PATH, 'shell', 'rm', '-rf', source_path]
        output = run_adb_command(command)
        
        # Füge hier Debugging-Ausgaben hinzu
        
        if output:  # Wenn es eine Ausgabe gibt, zeige sie an
            pass
            
        else:
            pass


def edit_files():
    global text_editor, editor_window, name_label
    total_files = len(selected_files_to_copy)

    if total_files == 0:
        messagebox.showwarning(texts['warning'], texts['noFilesSelectedForOpen'])
        return

    # Öffne den Texteditor nur, wenn er noch nicht geöffnet ist
    if editor_window is None or not tk.Toplevel.winfo_exists(editor_window):
        open_text_editor()

    text_editor.config(state=tk.NORMAL)
    text_editor.delete("1.0", tk.END)  # Löscht vorherige Ausgaben

    for index, file in enumerate(selected_files_to_copy):
        source_path = os.path.join(current_directory, file)
        source_path = f'"{source_path}"'  # Pfad in Anführungszeichen für adb-Befehl
        source_path2 = file

        # Führe adb shell cat aus, um die Datei zu kopieren
        command = [ADB_PATH, 'shell', 'cat', source_path]
        output = run_adb_command(command)

        # Anzeige des Dateinamens und der Trennlinie
        text_editor.insert(tk.END, f"Datei: {source_path2}\n", "filename")  # Dateiname in fett
        text_editor.insert(tk.END, "=" * 60 + "\n", "divider")  # Trennlinie

        # Ausgabe des Inhalts der Datei oder einer Fehlermeldung
        if output:
            text_editor.insert(tk.END, f"{output}\n\n", "content")  # Ausgabe mit Formatierung
        else:
            text_editor.insert(tk.END, "Fehler: Keine Daten verfügbar oder Fehler beim Ausführen des Befehls.\n\n", "error")

        # Label aktualisieren
        name_label.config(text=source_path2)

    text_editor.config(state=tk.DISABLED)  # Sperrt den Text-Editor am Ende

    # Debugging-Ausgabe in der Konsole für jede Datei
    print(f"Bearbeitung von {total_files} Dateien abgeschlossen.")

    # Debugging-Ausgabe in der Konsole für jede Datei
    print(f"Bearbeitung von {total_files} Dateien abgeschlossen.")

def format_size(bytes_size):
    """Konvertiert die Größe in Bytes in ein lesbares Format."""
    if bytes_size < 1024:
        return f"{bytes_size} B"
    elif bytes_size < 1024 ** 2:
        return f"{bytes_size / 1024:.2f} KB"
    elif bytes_size < 1024 ** 3:
        return f"{bytes_size / (1024 ** 2):.2f} MB"
    else:
        return f"{bytes_size / (1024 ** 3):.2f} GB"

def prop_files():
    """Hauptfunktion zur Verarbeitung der Dateien."""
    global name_value, path_value, size_value
    total_files = len(selected_files_to_copy)
    file_extensions = []

    for file in selected_files_to_copy:
        # Splitte den Dateinamen und die Erweiterung
        _, ext = os.path.splitext(file)
        file_extensions.append(ext)

    if total_files == 0:
        messagebox.showwarning(texts['warning'], texts['noFilesSelectedForOpen'])
        return

    for index, file in enumerate(selected_files_to_copy):
        source_path = os.path.join(current_directory, file)
        source_path1 = f'"{source_path}"'  # Pfad in Anführungszeichen für ADB-Befehl
        
        # Hole die Dateigröße in Kilobytes über den ADB-Befehl
        command = [ADB_PATH, 'shell', 'du', '-s', source_path1]

        try:
            output = subprocess.check_output(command, stderr=subprocess.STDOUT).decode().strip()
            # Extrahiere die Größe aus der Ausgabe
            bytes_size = int(output.split()[0]) * 1024  # ADB gibt die Größe in KB zurück, umwandeln in Bytes
            formatted_size = format_size(bytes_size)  # Größe umrechnen

            # Aktualisiere die Labels mit Dateiinformationen
            size_value.config(text=formatted_size)  # Anzeige in GUI aktualisieren
            name_value.config(text=file)
            type_value.config(text=file_extensions)
            path_value.config(text=source_path)

            create_tooltip(name_value, name_value.cget("text"))

            create_tooltip(type_value, type_value.cget("text"))

            create_tooltip(path_value, path_value.cget("text"))

        except subprocess.CalledProcessError as e:
            size_value.config(text="None")
              # Debugging-Ausgabe
        except ValueError:
            size_value.config(text="None")

        # Debugging-Ausgabe in der Konsole
        

def copy_path():
    # Holen Sie sich den Text aus dem Label
    text = path_value.config('text')[-1]  # Holen Sie sich den Text des Labels
    if text:
        root.clipboard_clear()  # Löschen Sie die aktuelle Zwischenablage
        root.clipboard_append(text)  # Fügen Sie den neuen Text zur Zwischenablage hinzu

def copy_name():
    # Holen Sie sich den Text aus dem Label
    text = name_value.config('text')[-1]  # Holen Sie sich den Text des Labels
    if text:
        root.clipboard_clear()  # Löschen Sie die aktuelle Zwischenablage
        root.clipboard_append(text)  # Fügen Sie den neuen Text zur Zwischenablage hinzu


       
        

def save_text():
    """Speichert den Text aus dem Texteditor in einer Datei."""
    file_path = filedialog.asksaveasfilename(
        defaultextension=".txt",
        filetypes=[(f"{texts['textfiles']}", "*.txt"), (f"{texts['allFiles']}", "*.*")]
    )
    
    if file_path:  # Wenn der Benutzer eine Datei ausgewählt hat
        try:
            with open(file_path, "w", encoding="utf-8") as file:
                file.write(text_editor.get("1.0", tk.END))
            messagebox.showinfo(texts['success'], texts['textSafe'])
        except Exception as e:
            messagebox.showerror(texts['error1'], f"{texts['ErrorSafe']} {e}")

def create_tooltip(widget, text):
    tooltip = None

    def show_tooltip(event):
        nonlocal tooltip
        if tooltip is not None:
            return  # Prevent multiple tooltips
        tooltip = tk.Toplevel(widget)  # Create a new window for the tooltip
        tooltip.wm_overrideredirect(True)  # Remove window decorations
        tooltip.wm_geometry(f"+{widget.winfo_rootx() + 20}+{widget.winfo_rooty() + 20}")  # Position tooltip

        label = tk.Label(tooltip, text=text, bg="yellow", bd=1, relief="solid")
        label.pack()

    def hide_tooltip(event):
        nonlocal tooltip
        if tooltip is not None:
            tooltip.destroy()  # Destroy the tooltip window
            tooltip = None

    # Bind the enter and leave events to the widget
    widget.bind("<Enter>", show_tooltip)
    widget.bind("<Leave>", hide_tooltip)

def open_text_editor():
    """Öffnet ein neues Texteditor-Fenster."""
    global text_editor, editor_window, name_label

    editor_window = tk.Toplevel(root)
    editor_window.title(texts['Title'])
    editor_window.geometry("800x750")
    editor_window.configure(bg="#282C34")

    try:
        img = Image.open(r"img\explorer.ico")
        img = img.resize((50, 50))  # Ändere die Größe nach Bedarf
        icon_photo = ImageTk.PhotoImage(img)
        editor_window.iconphoto(False, icon_photo)  # Setze das Icon für das Fenster
    except Exception as e:
        print(f"Fehler beim Laden des Icons: {e}")

    # Frame für den Texteditor mit schönem Design
    frame = ttk.Frame(editor_window, padding="10 10 10 10", style="My.TFrame")
    frame.place(relx=0.05, rely=0.05, relwidth=0.9, relheight=0.9)

    # Text-Widget im Frame erstellen
    text_editor = tk.Text(
        frame, wrap="word", undo=True, font=("Helvetica", 14),
        bg="#3C3F41", fg="#ABB2BF", insertbackground="white",
        relief="flat", selectbackground="#61AFEF", padx=10, pady=10
    )
    text_editor.place(relx=0, rely=0, relwidth=1, relheight=1)

    # Scrollbar hinzufügen
    scrollbar = ttk.Scrollbar(frame, orient="vertical", command=text_editor.yview)
    text_editor["yscrollcommand"] = scrollbar.set
    scrollbar.place(relx=0.98, rely=0, relheight=1)

    # Label für den Namen
    name_label = tk.Label(editor_window)
    name_label.place(relx=0.01, rely=0.01)

    # Download-Button mit Bild
    global download_ico
    download_img = Image.open(r"img\download.png")  # Ersetze mit dem Pfad zu deinem Bild
    download_ico = ImageTk.PhotoImage(download_img)

    download_text_button = tk.Button(
        editor_window, image=download_ico, height=24, width=24, command=save_text
    )
    download_text_button.place(relx=0.9, rely=0.01)

    # Stile für Toplevel und Text-Editor
    style = ttk.Style(root)
    style.configure("My.TFrame", background="#3C3F41", relief="solid")
    style.configure("My.TText", font=("Helvetica", 14), padding=5)

def create_top_level():
    top = Toplevel(root)
    top.title(texts['Info'])
    top.geometry("310x200")

    try:
        img = Image.open(r"img\explorer.ico")
        img = img.resize((50, 50))  # Ändere die Größe nach Bedarf
        icon_photo = ImageTk.PhotoImage(img)
        top.iconphoto(False, icon_photo)  # Setze das Icon für das Fenster
    except Exception as e:
        print(f"Fehler beim Laden des Icons: {e}")

    global name_value, path_value, type_value, size_value

    global download_ico
    global copy_ico  

    download_img = Image.open(r"img\download.png")  # Ersetze mit dem Pfad zu deinem Bild
    download_ico = ImageTk.PhotoImage(download_img)

    copy_img = Image.open(r"img\copy.png")  # Ersetze mit dem Pfad zu deinem Bild
    copy_ico = ImageTk.PhotoImage(copy_img)

    # Name Label und Button
    name_label = tk.Label(top, text=texts['Name'])
    name_label.place(relx=0.05, rely=0.1, anchor="w")
    
    name_value = tk.Label(top, text="")
    name_value.place(relx=0.3, rely=0.1, anchor="w")
    
    name_button = tk.Button(top, image=copy_ico, command=copy_name)
    name_button.place(relx=0.78, rely=0.1, anchor="w")

    name_button = tk.Button(top, image=download_ico, command=on_save_button_click)
    name_button.place(relx=0.89, rely=0.1, anchor="w")

    # Pfad Label und Button
    path_label = tk.Label(top, text=texts['Pfad'])
    path_label.place(relx=0.05, rely=0.3, anchor="w")
    
    path_value = tk.Label(top, text="")
    path_value.place(relx=0.3, rely=0.3, anchor="w")
    
    path_button = tk.Button(top, image=copy_ico, command=copy_path)
    path_button.place(relx=0.78, rely=0.3, anchor="w")

    # Typ Label und Button
    type_label = tk.Label(top, text=texts['typ'])
    type_label.place(relx=0.05, rely=0.5, anchor="w")
    
    type_value = tk.Label(top, text="")
    type_value.place(relx=0.3, rely=0.5, anchor="w")
    
    # Größe Label und Button
    size_label = tk.Label(top, text=texts['Size'])
    size_label.place(relx=0.05, rely=0.7, anchor="w")
    
    size_value = tk.Label(top, text="")
    size_value.place(relx=0.3, rely=0.7, anchor="w")
    
    

    prop_files()



def comp_files(local_path="/sdcard", archive_name="cool", archive_format="tar"):
    """Komprimiere die ausgewählten Dateien in ein Archiv."""
    total_files = len(selected_files_to_copy)
    
    if total_files == 0:
        messagebox.showwarning(texts['warning'], texts['noFilesSelectedForCopy'])
        return
    
    # Entferne führende Slashes in den Dateinamen, falls vorhanden
    cleaned_files = [file.lstrip("/") for file in selected_files_to_copy]
    
    # Wandle die Liste der bereinigten Dateien in einen Leerzeichen-getrennten String um
    files_to_compress = " ".join(cleaned_files)
    
    if not files_to_compress:
        messagebox.showwarning(texts['warning'], texts['noValidFilesForCompression'])
        return

    try:
        # Erstelle den ADB-Befehl basierend auf dem ausgewählten Format
        if archive_format == "tar":
            command = f"{ADB_PATH} shell tar -cvf {local_path}/{archive_name}.tar {current_directory}{files_to_compress}"
        elif archive_format == "gz":
            command = f"{ADB_PATH} shell busybox gzip -f {current_directory}{files_to_compress}"

        if archive_format == "bz2":
            command = f"{ADB_PATH} shell tar -cvjf {local_path}/{archive_name}.bz2 {current_directory}{files_to_compress}"
        
        if archive_format == "xz":
           command = f"{ADB_PATH} shell tar -cvf {local_path}/{archive_name}.xz {current_directory}{files_to_compress}"

        # Protokolliere den Befehl zur Überprüfung
        
        
        # Führe den ADB-Befehl aus
        output = run_adb_command(command)
        
        # Zeige den Output in der Konsole und in einer Messagebox an
    
        messagebox.showinfo("ADB Output", f"\n{output}")

        # Überprüfe das Ergebnis
        if "error" in output.lower():
            messagebox.showerror(texts['error1'], f"{texts['compressionError']} {output}")
        else:
            messagebox.showinfo(texts['success'], f"{texts['compressionSuccess']} {current_directory}{files_to_compress}.{archive_format}")
    except Exception as e:
        messagebox.showerror(texts['error1'], f"{texts['compressionError']} {str(e)}")

def apply_options(archive_name_entry, local_path_entry, archive_format_var, options_window):
    archive_name = archive_name_entry.get().strip()  # Benutzereingabe für den Archivnamen
    local_path = local_path_entry.get().strip()  # Benutzereingabe für den Speicherort
    archive_format = archive_format_var.get()  # Ausgewähltes Format
    
    if not archive_name:
        selected_files_to_copy()
        return
    
    if not local_path:
        messagebox.showwarning(texts['warning'], texts['selpfad'])
        return
    
    # Rufe die Funktion zum Komprimieren auf
    comp_files(local_path=local_path, archive_name=archive_name, archive_format=archive_format)
    options_window.destroy()  # Schließe das Optionen-Fenster nach der Anwendung

def open_options_window():
    options_window = tk.Toplevel(root)
    options_window.title(texts['option'])

    try:
        img = Image.open(r"img\explorer.ico")
        img = img.resize((50, 50))  # Ändere die Größe nach Bedarf
        icon_photo = ImageTk.PhotoImage(img)
        options_window.iconphoto(False, icon_photo)  # Setze das Icon für das Fenster
    except Exception as e:
        print(f"Fehler beim Laden des Icons: {e}")
    
    # Archivname
    tk.Label(options_window, text=texts['name2']).grid(row=0, column=0, padx=10, pady=5)
    archive_name_entry = tk.Entry(options_window)
    archive_name_entry.grid(row=0, column=1, padx=10, pady=5)
    
    # Speicherort
    tk.Label(options_window, text=texts['ort']).grid(row=1, column=0, padx=10, pady=5)
    local_path_entry = tk.Entry(options_window)
    local_path_entry.grid(row=1, column=1, padx=10, pady=5)
    
    # Format auswählen (TAR oder ZIP)
    tk.Label(options_window, text=texts['selectArchiveFormat']).grid(row=2, column=0, padx=10, pady=5)
    archive_formats = ["tar", "zip", "gz", "bz2", "xz", "7z", "rar"]
    archive_format_var = tk.StringVar(value=archive_formats[0])  # Standardwert
    archive_combobox = ttk.Combobox(options_window, textvariable=archive_format_var, values=archive_formats)
    archive_combobox.grid(row=2, column=1, padx=10, pady=5)
    
    # Anwenden-Button
    apply_button = tk.Button(options_window, text=texts['ok'], 
                             command=lambda: apply_options(archive_name_entry, local_path_entry, archive_format_var, options_window))
    apply_button.grid(row=3, column=1, pady=10)


    




def apply_options(archive_name_entry, local_path_entry, format_var, options_window):
    # Hole die eingegebenen Optionen
    archive_name = archive_name_entry.get()
    local_path = local_path_entry.get()
    archive_format = format_var.get()
    
    # Validierung: Archivname muss eingegeben werden
    if not archive_name:
        messagebox.showwarning(texts['error1'], texts['enterArchiveName'])
        return

    # Validierung: Speicherort muss eingegeben werden
    if not local_path:
        local_path = "/sdcard"  # Standardpfad, falls nichts angegeben wird
    
    # Schließe das Optionsfenster
    options_window.destroy()

    # Rufe die Komprimierungsfunktion auf
    comp_files(local_path, archive_name, archive_format)


def on_save_button_click():
    """Sichert die ausgewählten Dateien oder Verzeichnisse direkt auf den PC."""
    local_path = filedialog.askdirectory(title=texts['chooseDestinationFolder'])
    if not local_path:
        return  # Abbrechen, wenn kein Pfad ausgewählt wurde

    # Erstelle einen neuen Thread für das Kopieren der Dateien
    copy_files(local_path)


def update_path_display():
    """Aktualisiere die Anzeige des aktuellen Pfads."""
    path_label.config(text=f"{texts['Aktueller Pfad']} {current_directory}")
    children = directory_tree.get_children()
    item_count = len(children)

    # Beispiel für den Zugriff auf die letzten Einträge
    if item_count > 0:  # Überprüfe, ob es Kinder gibt
        directory_tree.see(children[-0]) # Scrolle zum letzten Eintrag

def on_sort_change(event):
    """Aktualisiere die Datei- und Ordnerliste, wenn sich die Sortieroption ändert."""
    sort_criterion = sort_var.get()
    update_file_list(current_directory, sort_criterion)

def show_tooltip(event, text):
    """Zeige Tooltip mit dem vollständigen Namen an."""
    global tooltip
    tooltip = tk.Toplevel(root)
    tooltip.wm_overrideredirect(True)
    tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")
    label = tk.Label(tooltip, text=text, background="yellow")
    label.pack()

def hide_tooltip(event):
    """Verstecke den Tooltip."""
    global tooltip
    if tooltip:
        tooltip.destroy()
        tooltip = None

def show_folders(folders):
    """Zeige die Ordner nebeneinander an."""
    for index, folder in enumerate(folders):
        folder_name = folder[0]
        short_name = folder_name[:10]  # Zeige nur die ersten 10 Zeichen
        full_name = folder_name

        # Erstelle einen Button für den Ordner
        button = ttk.Button(root, text=short_name, command=lambda f=folder: on_folder_click(f))
        button.grid(row=1, column=index, padx=5, pady=5)

        # Füge einen Tooltip hinzu, um den vollständigen Namen anzuzeigen
        button.bind("<Enter>", lambda e, name=full_name: show_tooltip(e, name))
        button.bind("<Leave>", hide_tooltip)

def on_folder_click(folder):
    """Verarbeite einen Klick auf den Ordner."""
    # Hier kannst du definieren, was passieren soll, wenn ein Ordner angeklickt wird.
    

def show_context_menu(event):
    """Zeige das Kontextmenü an."""
    try:
        # Hole das ausgewählte Element
        selected_item = directory_tree.selection()[0]
        selected_item_text = directory_tree.item(selected_item, "text")
        
        last_index = context_menu.index("end")
        if last_index is not None:
            # Durchsucht alle vorhandenen Einträge und löscht das `edit`-Kommando, wenn es existiert
            for i in range(last_index + 1):
                if context_menu.type(i) == "command" and context_menu.entrycget(i, "label") == texts['edit']:
                    context_menu.delete(i)
                    break

        if selected_item_text.endswith(".txt"):
            context_menu.add_command(label=texts['edit'], command=edit_files)

        # Kontextmenü nur anzeigen, wenn es mindestens einen Eintrag enthält
        if context_menu.index("end") is not None:
            context_menu.post(event.x_root, event.y_root)  # Menü anzeigen
            

       
        # Wenn es sich um eine Datei handelt, zeige das Kontextmenü
        if selected_item_text and not selected_item_text == '..':
            context_menu.post(event.x_root, event.y_root)
    except IndexError:
        context_menu.post(event.x_root, event.y_root)
    context_menu.unpost()





def push_files(selected_file):
    """Den Kopiervorgang in einem separaten Thread starten."""
    if selected_file:
        threading.Thread(target=push_copy, args=(selected_file,)).start()



def push_copy(selected_file):
    """Kopiere die ausgewählte Datei vom PC auf das Android-Gerät."""
    # Zielpfad auf dem Gerät angeben (zum Beispiel '/sdcard/Download/')
    for index, file in enumerate(selected_files_to_copy):
        source_path = os.path.join(current_directory)
        source_path = f'"{source_path}"'
        selected_file = f'"{selected_file}'

    # Führe adb push aus, um die Datei zu kopieren
    command = [ADB_PATH, 'push', selected_file, current_directory]
    output = run_adb_command(command)

    # Debugging-Ausgabe
    
    if output:  # Wenn es eine Ausgabe gibt, zeige sie an
        pass

    else:
        pass

    messagebox.showinfo(texts['success'], texts['fileCopiedToDevice'])
    update_file_list(current_directory)


def open_toplevel():
    global name_entry, path_entry

    """Öffnet ein Toplevel-Fenster mit zwei Entry-Feldern."""
    for index, file in enumerate(selected_files_to_copy):
        source_path = os.path.join(current_directory)
        source_path = f'"{source_path}"'
    
    Standart_name = "New Folder"        

    toplevel = tk.Toplevel(root)
    toplevel.title("Informationen eingeben")

    try:
        img = Image.open(r"img\explorer.ico")
        img = img.resize((50, 50))  # Ändere die Größe nach Bedarf
        icon_photo = ImageTk.PhotoImage(img)
        toplevel.iconphoto(False, icon_photo)  # Setze das Icon für das Fenster
    except Exception as e:
        print(f"Fehler beim Laden des Icons: {e}")
    
    # Label und Entry für den Namen
    name_label = tk.Label(toplevel, text=texts['Name'])
    name_label.pack(pady=5)
    
    name_entry = tk.Entry(toplevel, width=30)
    name_entry.pack(pady=5)
    name_entry.insert(0, Standart_name)

    # Label und Entry für den Pfad
    path_label = tk.Label(toplevel, text=texts['Pfad'])
    path_label.pack(pady=5)

    path_entry = tk.Entry(toplevel, width=30)
    path_entry.pack(pady=5)
    path_entry.insert(0, current_directory)


    # Create-Button, um eine Nachricht anzuzeigen
    create_button = tk.Button(toplevel, text=texts['Create'], command=create_directory)
    create_button.pack(pady=10)

def create_directory():
    """Kopiere die ausgewählte Datei vom PC auf das Android-Gerät."""
    # Zielpfad auf dem Gerät angeben (zum Beispiel '/sdcard/Download/')
    name = name_entry.get()  # Abrufen der Eingabe aus dem Namen-Entry
    path = path_entry.get()

    # Führe adb push aus, um die Datei zu kopieren
    
    command = [ADB_PATH, 'shell', 'mkdir', f'"{path}/{name}"']

    output = run_adb_command(command)

    # Debugging-Ausgabe
    
    if output:  # Wenn es eine Ausgabe gibt, zeige sie an
        pass

    else:
        pass
    update_file_list(current_directory)
def rename_toplevel():
    global rename_entry

    """Öffnet ein Toplevel-Fenster mit zwei Entry-Feldern."""
    for index, file in enumerate(selected_files_to_copy):
        source_path = os.path.join(current_directory)
        source_path = f'"{source_path}"'
    
    Standart_name = "New Folder"        

    toplevel = tk.Toplevel(root)
    toplevel.title("Informationen eingeben")
    
    # Label und Entry für den Namen
    name_label = tk.Label(toplevel, text=texts['Name'])
    name_label.pack(pady=5)
    
    rename_entry = tk.Entry(toplevel, width=30)
    rename_entry.pack(pady=5)

    rename_button = tk.Button(toplevel, text=texts['Rename'], command=rename_files)
    rename_button.pack(pady=10)
    
def rename_files():
    """Kopiere die ausgewählten Dateien oder Verzeichnisse in den Zielordner."""
    total_files = len(selected_files_to_copy)
    name = rename_entry.get()  # Neuen Namen aus dem Entry-Feld abrufen

    if total_files == 0:
        pass
        return

    for index, file in enumerate(selected_files_to_copy):
        source_path = os.path.join(current_directory, file)

        # Hole die Dateiendung
        _, file_extension = os.path.splitext(file)

        # Setze den neuen Dateinamen zusammen
        new_name = f"{name}{file_extension}"  # Neuen Namen mit der ursprünglichen Erweiterung
        destination_path = os.path.join(current_directory, new_name)

        # Führe adb shell mv aus, um die Dateien umzubenennen
        command = [ADB_PATH, 'shell', 'mv', f'"{source_path}"', f'"{destination_path}"']
        output = run_adb_command(command)

        # Füge hier Debugging-Ausgaben hinzu

    update_file_list(current_directory)

def push_selected_file():
    """Wählt eine Datei oder einen Ordner vom PC aus und kopiert sie auf das Gerät."""
    # Wählen Sie zwischen Datei oder Ordner
    choice = messagebox.askquestion("Wählen Sie aus", "File = Yes\nFolder=NO", icon='question')
    
    if choice == 'yes':
        # Datei auswählen
        selected_file = filedialog.askopenfilename(title="Wählen Sie eine Datei aus")
        
        if selected_file:
            push_files(selected_file)  # Datei kopieren
        else:
            return  # Abbrechen, wenn keine Datei ausgewählt wurde
    else:
        # Ordner auswählen
        selected_file = filedialog.askdirectory(title="Wählen Sie einen Ordner aus")
        
        if selected_file:
            push_files(selected_file)  # Ordner kopieren
        else:
            return  # Abbrechen, wenn kein Ordner ausgewählt wurde

def copy_selected_file():
    """Kopiere die ausgewählte Datei."""
    local_path = filedialog.askdirectory(title="")
    if not local_path:
        return  # Abbrechen, wenn kein Pfad ausgewählt wurde
    
    copy_files(local_path)



def compress_selected_file():
    """Kopiere die ausgewählte Datei."""
    local_path = "/sdcard"
    if not local_path:
        return  # Abbrechen, wenn kein Pfad ausgewählt wurde
    
    comp_files(local_path)

def Del_selected_file():
    """Kopiere die ausgewählte Datei."""
    local_path = ()

    
    Start_Del_files()

def get_file_properties(file_path):
    """Erhalte Dateieigenschaften (Größe, Datum) von einem Gerät über ADB."""
    try:
        # ADB Befehl, um Dateieigenschaften zu erhalten
        command = f"{ADB_PATH} shell ls -l '{file_path}'"
        result = subprocess.run(command, capture_output=True, text=True, shell=True)

        if result.returncode == 0:
            # Ausgabe: '-rw-r--r-- 1 root root 4096 Apr  8 10:22 file.txt'
            output = result.stdout.strip()
            parts = output.split()
            if len(parts) >= 8:
                file_size = parts[4]  # Die Dateigröße ist normalerweise an 5. Stelle
                modification_date = ' '.join(parts[5:8])  # Änderungsdatum und Zeit

                return {
                    "size": file_size,
                    "modification_date": modification_date
                }
            else:
                return None  # Unzureichende Daten zurückgegeben
        else:
            return None
    except Exception as e:
        pass
        return None





# Setze das Startverzeichnis auf /
current_directory = ''

# Variable für die ausgewählten Dateien
selected_files_to_copy = []
tooltip = None

# Erstelle das Tkinter-Fenster
root = tk.Tk()
root.title("File Explorer")
root.geometry("600x500")  # Fenstergröße
root.configure(bg="#2E2E2E")  # Hintergrundfarbe des Fensters

try:
    img = Image.open(r"img\explorer.ico")
    img = img.resize((50, 50))  # Ändere die Größe nach Bedarf
    icon_photo = ImageTk.PhotoImage(img)
    root.iconphoto(False, icon_photo)  # Setze das Icon für das Fenster
except Exception as e:
    print(f"Fehler beim Laden des Icons: {e}")

sort_var = tk.StringVar(value=sort_options[0])  # Standardwert
sort_menu = ttk.OptionMenu(root, sort_var, sort_options[0], *sort_options, command=on_sort_change)
sort_menu.pack()

        # Übersetzungen und Texte laden
language_code = load_language_setting()
translations = load_translations()
texts = get_texts(language_code)

# Lade die Symbole für Ordner und Dateien
folder_icon = PhotoImage(file=r"img\folder.png")  # Pfad zum Ordner-Symbol (PNG)
file_icon = PhotoImage(file=r"img\document.png")      # Pfad zum Datei-Symbol (PNG)

# Erstelle eine Treeview für die Anzeige der Dateien mit Symbolen
directory_tree = ttk.Treeview(root, columns=("full_path",), show="tree", selectmode="extended")
directory_tree.place(relx=0.5, rely=0.45, anchor="center", relwidth=0.9, relheight=0.7)

# Binde Doppelklick-Ereignisse

directory_tree.bind("<Double-1>", on_treeview_double_click)
directory_tree.bind("<<TreeviewSelect>>", on_treeview_select)

# Label für den aktuellen Pfad
path_label = tk.Label(root, text=f"{texts['Aktueller Pfad']} {current_directory}", bg="#2E2E2E", fg="white", font=("Arial", 12))
path_label.place(relx=0.05, rely=0.98, anchor="w")  # Position des Pfad-Labels

# Fortschrittsanzeige erstellen
progress_var = tk.DoubleVar()  # Fortschrittsvariable

# Progress-Bar hinzufügen
progress_bar = ttk.Progressbar(root, orient="horizontal", length=300, mode="determinate", variable=progress_var)
progress_bar.place_forget()

# Aktualisiere die Dateiliste mit dem Startverzeichnis
update_file_list(current_directory)

directory_tree.bind("<Button-3>", show_context_menu)

style = ttk.Style()
style.configure("Custom.TLabelframe", background="black")
style.configure("Custom.TLabelframe.Label", background="red", foreground="black")


# Kontextmenü erstellen
context_menu = Menu(root, tearoff=0)
context_menu.add_command(label=texts['copy'], command=copy_selected_file)
context_menu.add_command(label=texts['paste'], command=push_selected_file)
context_menu.add_command(label=texts['delete'], command=Del_selected_file)
context_menu.add_separator()
context_menu.add_command(label=texts['createFolder'], command=open_toplevel)
context_menu.add_command(label=texts['Rename'], command=rename_toplevel)
context_menu.add_separator()
context_menu.add_command(label=texts['compress'], command=open_options_window)
context_menu.add_command(label=texts['properties'], command=create_top_level) 

# Erstelle einen Button, um in das vorherige Verzeichnis zu gehen
back_button = tk.Button(root, text=texts['back'], command=on_back_button_click, bg="#666666", fg="white", font=("Arial", 12))
back_button.pack(side="right",anchor="ne", padx=5)

fast_save_button = tk.Button(root, text=texts['schnellesSichern'], command=open_fast_frame, bg="#666666", fg="white", font=("Arial", 12))
fast_save_button.pack(side="right",anchor="ne", padx=5)

# Erstelle einen Button, um Dateien zu speichern
save_button = tk.Button(root, text=texts['copy'], command=on_save_button_click, bg="#666666", fg="white", font=("Arial", 12))
save_button.pack(side="right",anchor="ne", padx=5)



# Starte die Tkinter-Hauptschleife
root.mainloop()

