import requests
import os
from PIL import Image, ImageDraw, ImageFont
import shutil
import tkinter as tk
from tkinter import filedialog

def restore_backups(base_dir: str):
    """
    If a backup exists (backup_<name>.png), copy it over the original image.png, then delete the backup.
    If no backup exists, print a warning.
    """
    missing_backups = 0

    for folder_name in os.listdir(base_dir):
        folder_path = os.path.join(base_dir, folder_name)
        if not os.path.isdir(folder_path):
            continue

        for file_name in os.listdir(folder_path):
            if not file_name.lower().endswith(".png"):
                continue
            if file_name.startswith("backup_"):
                # skip backup files themselves in this loop
                continue

            img_path = os.path.join(folder_path, file_name)
            backup_path = os.path.join(folder_path, f"backup_{file_name}")

            if os.path.exists(backup_path):
                try:
                    # Restore backup → overwrite original
                    shutil.copy2(backup_path, img_path)
                    print(f"[RESTORED] {file_name} <- backup_{file_name}")

                    # Delete the backup after successful restore
                    os.remove(backup_path)
                except Exception as e:
                    print(f"[ERROR] Failed to restore {file_name}: {e}")
            else:
                print(f"[WARN] No backup found for {file_name}")
                missing_backups += 1

    print(f"\nRestore complete: {missing_backups} missing backups.")

def draw_jacket(img, chart_list):
    draw = ImageDraw.Draw(img)
    width, height = img.size

    margin_ratio = 0.07 

    # Scale font by image height
    font_size = int(height * 0.08)
    try:
        font = ImageFont.truetype("arial.ttf", font_size)
    except OSError:
        font = ImageFont.load_default()

    margin = int(height * margin_ratio)

    difficulty_colors = {
        'MXM': (192, 192, 192, 255),
        'XCD': (0, 128, 255, 255),
        'GRV': (255, 153, 51, 255),
        'EXH': (255, 73, 73, 255),
        'INF': (255, 102, 255, 255),
        'VVD': (255, 51, 255, 255),
        'ULT': (255, 255, 0, 255),
        'HVN': (51, 255, 255, 255),
    }

    line_height = (font.getbbox("Ag")[3] - font.getbbox("Ag")[1]) * 1.1

    text_x = margin
    text_y = margin

    # Draw each line with its corresponding color
    for i, chart in enumerate(chart_list):
        sTier = chart.get('sTier')
        pucTier = chart.get('pucTier')

        # Determine display text depending on what exists
        if sTier is not None and pucTier is not None:
            line_text = f"{sTier:.1f}S-{pucTier:.1f}P"
        elif sTier is not None:
            line_text = f"{sTier:.1f}S"
        elif pucTier is not None:
            line_text = f"{pucTier:.1f}P"
        else:
            continue
            
        fill_color = difficulty_colors.get(chart.get('difficulty'), (255, 255, 255, 255))

        draw.text(
            (text_x, text_y + i * line_height),
            line_text,
            font=font,
            fill=fill_color,
            stroke_width=max(int(font_size * 0.1), 1),
            stroke_fill=(0, 0, 0, 255)
        )

    return img

def tier_jacket(base_dir: str, chart_data: dict):
    """
    If a backup doesn't exist, create one and annotate the original.
    If a backup exists, use it as the base and overwrite the normal PNG.
    """
    for folder_name in os.listdir(base_dir):
        folder_path = os.path.join(base_dir, folder_name)
        if not os.path.isdir(folder_path):
            continue

        # Extract numeric ID prefix
        try:
            in_game_id = int(folder_name.split("_")[0])
        except (ValueError, IndexError):
            continue

        if in_game_id not in chart_data:
            continue

        for file_name in os.listdir(folder_path):
            if not file_name.lower().endswith(".png"):
                continue
            if file_name.startswith("backup_"):
                continue

            img_path = os.path.join(folder_path, file_name)
            backup_path = os.path.join(folder_path, f"backup_{file_name}")

            # Use backup if exists, otherwise create one
            if os.path.exists(backup_path):
                base_image_path = backup_path
                print(f"[USE BACKUP] Using {backup_path}")
            else:
                try:
                    os.makedirs(os.path.dirname(backup_path), exist_ok=True)
                    shutil.copy2(img_path, backup_path)
                    print(f"[BACKUP] {file_name} -> backup_{file_name}")
                    base_image_path = backup_path
                except Exception as e:
                    print(f"[ERROR] Failed to create backup for {file_name}: {e}")
                    continue

            # Open and write
            try:
                img = Image.open(base_image_path).convert("RGBA")
            except Exception as e:
                print(f"[ERROR] Failed to open {base_image_path}: {e}")
                continue

            img = draw_jacket(img, chart_data[in_game_id])
            img.save(img_path)
            print(f"[OK] Edited {file_name}")

    print("All jackets edited.")

def fetch_tier(github_url: str = "https://raw.githubusercontent.com/zkrising/Tachi/refs/heads/main/seeds/collections/charts-sdvx.json"):
    print("Fetching charts info")
    response = requests.get(github_url)
    response.raise_for_status()
    
    charts = response.json()
    result = {}
    
    for entry in charts:
        in_game_id = entry["data"].get("inGameID")
        difficulty = entry.get("difficulty")
        
        s_tier = entry["data"].get("sTier")
        s_tier_value = s_tier.get("value") if s_tier else None

        puc_tier = entry["data"].get("pucTier")
        puc_tier_value = puc_tier.get("value") if puc_tier else None

        if s_tier_value is None and puc_tier_value is None:
            continue
        if in_game_id is None:
            continue 
        
        if in_game_id not in result:
            result[in_game_id] = []
        
        result[in_game_id].append({
            "difficulty": difficulty,
            "sTier": s_tier_value,
            "pucTier": puc_tier_value
        })
    
    return result

def select_folder():
    """Open a folder selection dialog and return the chosen path."""
    root = tk.Tk()
    root.withdraw()  # Hide the main window
    folder_selected = filedialog.askdirectory(title="Select Target Folder")
    root.destroy()
    return folder_selected

def main():
    print("1. Draw S Tier info")
    print("2. Draw PUC Tier info")
    print("3. Draw S + PUC Tier info")
    print("4. Restore backups")
    choice = input("Select an option: ").strip()

    if choice not in {"1", "2", "3", "4"}:
        print("It's not that hard to type a number man")
        return

    print("Select music folder (should be /contents/data/music)")
    folder = select_folder()
    if not folder:
        print("No folder selected. Exiting.")
        return

    if choice == "4":
        restore_backups(folder)
        return

    data = fetch_tier()

    if choice == "1":
        for k, charts in data.items():
            for c in charts:
                c["pucTier"] = None  # remove puc tier data
        tier_jacket(folder, data)

    elif choice == "2":
        for k, charts in data.items():
            for c in charts:
                c["sTier"] = None  # remove s tier data
        tier_jacket(folder, data)

    elif choice == "3":
        tier_jacket(folder, data)


if __name__ == "__main__":
    main()

