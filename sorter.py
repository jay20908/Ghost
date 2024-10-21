import os
import shutil
import schedule
import time

def move_file(file_path, destination_folder):
    os.makedirs(destination_folder, exist_ok=True)
    shutil.move(file_path, os.path.join(destination_folder, os.path.basename(file_path)))

def scan_and_organize_downloads():
    downloads_folder = os.path.expanduser("~/Downloads")
    video_folder = os.path.expanduser("~/Videos")
    zip_folder = os.path.expanduser("~/ZipFiles")
    iso_folder = os.path.expanduser("~/ISOFiles")
    rar_folder = os.path.expanduser("~/RARFiles")
    img_folder = os.path.expanduser("~/Images")
    doc_folder = os.path.expanduser("~/Documents")
    exe_folder = os.path.expanduser("~/EXEFiles")
    apk_folder = os.path.expanduser("~/APKFiles")
    msi_folder = os.path.expanduser("~/APKFiles")

    

    for filename in os.listdir(downloads_folder):
        file_path = os.path.join(downloads_folder, filename)
        if os.path.isfile(file_path):
            _, extension = os.path.splitext(filename)
            extension = extension.lower()

            if extension in ['.mp4', '.avi', '.mkv', '.mov']:
                move_file(file_path, video_folder)
            elif extension == '.zip':
                move_file(file_path, zip_folder)
            elif extension == '.iso':
                move_file(file_path, iso_folder)
            elif extension == '.rar':
                move_file(file_path, rar_folder)
            elif extension in ['.jpg', '.png', '.jpeg', '.gif', '.bmp', '.tiff', '.webp']:
                move_file(file_path, img_folder)
            elif extension in ['.doc', '.docx', '.pdf', '.txt', '.rtf', '.odt', '.xls', '.xlsx', '.ppt', '.pptx']:
                move_file(file_path, doc_folder)
            elif extension == '.exe':
                move_file(file_path, exe_folder)
            elif extension == '.msi':
                move_file(file_path, msi_folder)
            elif extension == '.apk':
                move_file(file_path, apk_folder)

    print(f"Scanned and organized files in {downloads_folder}")

def main():
    # Run the scan immediately when the script starts
    scan_and_organize_downloads()
    
    
    

if __name__ == '__main__':
    main()
