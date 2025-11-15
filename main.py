import requests
import os
import json
import shutil

# === Settings ===
PAGE_ACCESS_TOKEN = os.getenv("PAGE_ACCESS_TOKEN")
PAGE_ID = os.getenv("PAGE_ID")

COMMENTS_BASE_FOLDER = "comments"
POSTED_FOLDER = os.path.join(COMMENTS_BASE_FOLDER, "posted")
FOLDER_COUNT = 3  # total number of folders to rotate

# Ensure posted folder exists
os.makedirs(POSTED_FOLDER, exist_ok=True)

# Track last processed post
last_post_id_file = os.path.join(COMMENTS_BASE_FOLDER, "last_post_id.txt")
folder_rotation_file = os.path.join(COMMENTS_BASE_FOLDER, "folder_rotation.txt")

# Ensure tracking files exist with default content
os.makedirs(COMMENTS_BASE_FOLDER, exist_ok=True)
if not os.path.exists(last_post_id_file):
    with open(last_post_id_file, "w") as f:
        f.write("")  # empty initially

if not os.path.exists(folder_rotation_file):
    with open(folder_rotation_file, "w") as f:
        f.write("1")  # start from folder 1


def get_last_post_id():
    with open(last_post_id_file, "r") as f:
        return f.read().strip() or None


def save_last_post_id(post_id):
    with open(last_post_id_file, "w") as f:
        f.write(post_id)


def get_latest_post_id():
    url_feed = f"https://graph.facebook.com/v19.0/{PAGE_ID}/feed"
    params = {"access_token": PAGE_ACCESS_TOKEN, "limit": 1}
    response = requests.get(url_feed, params=params)
    feed = response.json()
    if "data" in feed and feed["data"]:
        return feed["data"][0]["id"]
    return None


def get_folder_rotation():
    with open(folder_rotation_file, "r") as f:
        content = f.read().strip()
        if content.isdigit():
            return int(content)
    return 1  # default to folder 1 if missing or invalid


def save_folder_rotation(rotation):
    with open(folder_rotation_file, "w") as f:
        f.write(str(rotation))


def post_comments_for_post(post_id, folder_number):
    folder_path = os.path.join(COMMENTS_BASE_FOLDER, str(folder_number))
    if not os.path.exists(folder_path):
        print(f"⚠️ Folder {folder_number} does not exist, skipping comments.")
        return

    image_files = [
        f for f in os.listdir(folder_path)
        if f.lower().endswith((".png", ".jpg", ".jpeg"))
    ]

    if not image_files:
        print(f"⚠️ No images in folder {folder_number}, skipping.")
        return

    for image_name in image_files:
        image_path = os.path.join(folder_path, image_name)
        url_comment = f"https://graph.facebook.com/v19.0/{post_id}/comments"

        with open(image_path, "rb") as f:
            image_data = f.read()

        files = {"source": (image_name, image_data)}
        params = {"access_token": PAGE_ACCESS_TOKEN}

        print(f"📤 Uploading comment: {image_name} ...")
        response = requests.post(url_comment, files=files, data=params)
        result = response.json()
        print(json.dumps(result, indent=2))

        if "id" in result:
            print(f"✅ Comment posted successfully: {image_name}")
            shutil.move(image_path, os.path.join(POSTED_FOLDER, image_name))
        else:
            print(f"❌ Failed to post comment: {image_name}")


# === Main execution ===
def main():
    latest_post_id = get_latest_post_id()
    last_post_id = get_last_post_id()
    folder_rotation = get_folder_rotation()

    if latest_post_id and latest_post_id != last_post_id:
        print(f"🆕 New post detected: {latest_post_id}")
        post_comments_for_post(latest_post_id, folder_rotation)
        save_last_post_id(latest_post_id)

        # Rotate folder for next new post
        folder_rotation += 1
        if folder_rotation > FOLDER_COUNT:
            folder_rotation = 1
        save_folder_rotation(folder_rotation)

    else:
        print("ℹ️ No new post detected.")


if __name__ == "__main__":
    main()
