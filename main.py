import requests
import os
import json
import shutil

# === Settings ===
PAGE_ACCESS_TOKEN = os.environ.get("PAGE_ACCESS_TOKEN")  # from GitHub Secrets
PAGE_ID = os.environ.get("PAGE_ID")  # also from Secrets
COMMENTS_BASE_FOLDER = "comments"
POSTED_FOLDER = os.path.join(COMMENTS_BASE_FOLDER, "posted")

# Ensure posted folder exists
os.makedirs(POSTED_FOLDER, exist_ok=True)

# Track last processed post
last_post_id_file = "last_post_id.txt"


def get_last_post_id():
    if os.path.exists(last_post_id_file):
        with open(last_post_id_file, "r") as f:
            return f.read().strip()
    return None


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


def post_comments_for_post(post_id):
    # Only one folder per run — rotate based on post ID hash
    folder_number = (hash(post_id) % 3) + 1
    folder_path = os.path.join(COMMENTS_BASE_FOLDER, str(folder_number))

    if not os.path.exists(folder_path):
        print(f"⚠️ Folder {folder_number} does not exist, skipping.")
        return

    image_files = [
        f for f in os.listdir(folder_path)
        if f.lower().endswith(('.png', '.jpg', '.jpeg'))
    ]

    for image_name in image_files:
        image_path = os.path.join(folder_path, image_name)

        with open(image_path, "rb") as f:
            image_data = f.read()

        url_comment = f"https://graph.facebook.com/v19.0/{post_id}/comments"
        files = {'source': (image_name, image_data)}
        params = {'access_token': PAGE_ACCESS_TOKEN}

        print(f"📤 Uploading comment: {image_name} ...")
        res = requests.post(url_comment, files=files, data=params).json()
        print(json.dumps(res, indent=2))

        if "id" in res:
            print(f"✅ Posted: {image_name}")
            shutil.move(image_path, os.path.join(POSTED_FOLDER, image_name))
        else:
            print(f"❌ Failed: {image_name}")


def main():
    latest_post_id = get_latest_post_id()
    last_post_id = get_last_post_id()

    if latest_post_id and latest_post_id != last_post_id:
        print(f"🆕 New post detected: {latest_post_id}")
        post_comments_for_post(latest_post_id)
        save_last_post_id(latest_post_id)
    else:
        print("ℹ️ No new post.")


if __name__ == "__main__":
    main()
