from flask import Flask, render_template, request, redirect, url_for
import json
from collections import Counter
from datetime import datetime
import re

app = Flask(__name__)

def to_datetime(date_str):
    return datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')

def format_date(dt):
    dt = to_datetime(dt)
    return dt.strftime('%I:%M:%S %p  ' + '  %m/%d/%Y')

def extract_tags(comment_text):
    return re.findall(r'@[\w]+', comment_text)

def analyze_json(json_data):
    stats = {}

    liked_videos = json_data.get("Activity", {}).get("Favorite Videos", {}).get("FavoriteVideoList", [])
    if liked_videos and isinstance(liked_videos, list):
        first_liked_video = min(liked_videos, key=lambda x: to_datetime(x['Date']))
        stats["First liked video date and time"] = format_date(first_liked_video['Date'])

    favorite_sounds = json_data.get("Activity", {}).get("Favorite Sounds", {}).get("FavoriteSoundList", [])
    if favorite_sounds and isinstance(favorite_sounds, list):
        first_favorited_sound = min(favorite_sounds, key=lambda x: to_datetime(x['Date']))
        stats["First favorited sound date and time"] = format_date(first_favorited_sound['Date'])

    if liked_videos:
        first_favorited_video = min(liked_videos, key=lambda x: to_datetime(x['Date']))
        stats["First favorited video date and time"] = format_date(first_favorited_video['Date'])

    logins = json_data.get("Activity", {}).get("Login History", {}).get("LoginHistoryList", [])
    if logins and isinstance(logins, list):
        login_dates = [to_datetime(login['Date']).date() for login in logins]
        login_count_by_day = Counter(login_dates)
        most_logins_day = login_count_by_day.most_common(1)[0]
        stats["Most amount of log-ins in a day"] = most_logins_day[1]
        stats["Total number of logins"] = len(logins)
        stats["Earliest log-in"] = min(login_dates)
        stats["Most recent log-in"] = max(login_dates)
    else:
        print("no_logins for some reason")

    shared_videos = json_data.get("Activity", {}).get("Share History", {}).get("ShareHistoryList", [])
    if shared_videos and isinstance(shared_videos, list):
        first_shared_video = min(shared_videos, key=lambda x: to_datetime(x['Date']))
        stats["First shared video date and time"] = format_date(first_shared_video['Date'])

    viewed_videos = json_data.get("Activity", {}).get("Video Browsing History", {}).get("VideoList", [])
    if viewed_videos and isinstance(viewed_videos, list):
        first_viewed_video = min(viewed_videos, key=lambda x: to_datetime(x['Date']))
        most_recent_viewed_video = max(viewed_videos, key=lambda x: to_datetime(x['Date']))
        stats["First viewed video date and time"] = format_date(first_viewed_video['Date'])
        stats["Most recent viewed video date and time"] = format_date(most_recent_viewed_video['Date'])
        stats["Total number of videos watched"] = len(viewed_videos)


    comments = json_data.get("Comment", {}).get("Comments", {}).get("CommentsList", [])
    if comments and isinstance(comments, list):
        first_comment = min(comments, key=lambda x: to_datetime(x['Date']))
        most_recent_comment = max(comments, key=lambda x: to_datetime(x['Date']))
        total_comments = len(comments)

        all_tags = []
        for comment in comments:
            comment_text = comment.get('Comment', '')
            tags_in_comment = extract_tags(comment_text)
            all_tags.extend(tags_in_comment)

        most_common_tag = Counter(all_tags).most_common(1)

        stats["First comment"] = first_comment.get('Comment', 'No comment text found')
        stats["First comment date"] = format_date(first_comment['Date'])
        stats["Most recent comment"] = most_recent_comment.get('Comment', 'No comment text found')
        stats["Most recent comment date"] = format_date(most_recent_comment['Date'])
        stats["Total number of comments"] = total_comments
        stats["Most common @tag"] = most_common_tag[0][0] if most_common_tag else "No @tags found"

    
    stats["Total number of shares"] = len(shared_videos)

    stats["Total number of favorited sounds"] = len(favorite_sounds)
    stats["Total number of favorited videos"] = len(liked_videos)

    private_messages = json_data.get("Direct Messages", {}).get("Chat History", {}).get("ChatHistory", [])
    if private_messages and isinstance(private_messages, list):
        messages_by_day = Counter([to_datetime(msg['Date']).date() for msg in private_messages])
        most_messages_in_day = messages_by_day.most_common(1)[0]
        stats["Most amount of messages in a private DM"] = most_messages_in_day[1]

    shop_views = json_data.get("Tik Tok Shopping", {}).get("Product Browsing History", {}).get("ProductBrowsingHistories", [])
    if shop_views and isinstance(shop_views, list):
        first_shop_product = min(shop_views, key=lambda x: to_datetime(x['Date']))
        stats["First TikTok shop product viewed"] = first_shop_product.get('ProductName', 'No product name found')
        stats["First shop product viewed date"] = format_date(first_shop_product['Date'])

    return stats


@app.route('/')
def home():
    return render_template('index.html', show_run_button=False)

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return redirect(request.url)

    file = request.files['file']
    if file.filename == '':
        return redirect(request.url)

    if file:
        file_data = file.read().decode("utf-8")
        json_data = json.loads(file_data)

        with open('uploaded_file.json', 'w') as f:
            f.write(file_data)
        return render_template('index.html', show_run_button=True)

@app.route('/analyze', methods=['POST'])
def analyze_file():
    with open('uploaded_file.json', 'r') as f:
        json_data = json.load(f)
    stats = analyze_json(json_data)
    return render_template('index.html', stats=stats, show_run_button=True)

if __name__ == '__main__':
    app.run(debug=True)
