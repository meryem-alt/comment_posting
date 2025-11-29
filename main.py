import os
import json
import requests
import time

PAGE_ACCESS_TOKEN = os.getenv("PAGE_ACCESS_TOKEN")
PAGE_ID = os.getenv("PAGE_ID")


# -------------------------------
# Helpers
# -------------------------------

def load_status():
    if not os.path.exists("status.json"):
        return {"last_story": 0}

    with open("status.json", "r") as f:
        return json.load(f)


def save_status(data):
    with open("status.json", "w") as f:
        json.dump(data, f)


def post_facebook_image(image_path):
    url = f"https://graph.facebook.com/v19.0/{PAGE_ID}/photos"
    files = {"source": open(image_path, "rb")}
    params = {"access_token": PAGE_ACCESS_TOKEN}

    res = requests.post(url, files=files, data=params).json()

    if "post_id" in res:
        print("✅ Posted main image:", image_path)
        return res["post_id"]

    print("❌ Failed posting main image:", res)
    return None


def post_comment_image(post_id, image_path):
    url = f"https://graph.facebook.com/v19.0/{post_id}/comments"
    files = {"source": open(image_path, "rb")}
    params = {"access_token": PAGE_ACCESS_TOKEN}

    res = requests.post(url, files=files, data=params).json()

    if "id" in res:
        print("🟢 Comment posted:", image_path)
        return True

    print("❌ Comment failed:", res)
    return False


# -------------------------------
# MAIN LOGIC
# -------------------------------

def main():
    status = load_status()
    last_story = status.get("last_story", 0)

    # -----------------------------
    # CHECK FOR NEXT STORY
    # -----------------------------
    stories = sorted([
        int(f.split(".")[0])
        for f in os.listdir("mainstories")
        if f.endswith((".png", ".jpg", ".jpeg"))
    ])

    if not stories:
        print("❌ No stories found in mainstories/")
        return

    # Find the next story to post
    next_story = None
    for s in stories:
        if s > last_story:
            next_story = s
            break

    if next_story is None:
        print("✨ No new story to publish. Waiting next run...")
        return

    print(f"📌 Starting Story #{next_story}")

    # -----------------------------
    # POST MAIN STORY
    # -----------------------------
    main_image_path = f"mainstories/{next_story}.png"
    post_id = post_facebook_image(main_image_path)

    if not post_id:
        print("❌ Cannot continue without main post.")
        return

    # -----------------------------
    # POST ALL COMMENTS IMAGES
    # -----------------------------
    comments_folder = f"comments/{next_story}"

    if not os.path.exists(comments_folder):
        print(f"⚠️ No comments folder for story {next_story}. Skipping...")
    else:
        images = sorted([
            f for f in os.listdir(comments_folder)
            if f.lower().endswith((".png", ".jpg", ".jpeg"))
        ])

        for img in images:
            img_path = os.path.join(comments_folder, img)
            post_comment_image(post_id, img_path)
            time.sleep(1)

    # -----------------------------
    # UPDATE STATUS
    # -----------------------------
    status["last_story"] = next_story
    save_status(status)

    print(f"🎉 Story {next_story} Completed!")


if __name__ == "__main__":
    main()
