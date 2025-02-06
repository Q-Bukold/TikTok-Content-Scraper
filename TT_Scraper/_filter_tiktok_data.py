from datetime import datetime
import time

def _force_to_int(self, value):
    """
    Given a value, returns the value as an int if possible.
    Otherwise returns None.
    """
    try:
        return int(value)
    except (ValueError, TypeError):
        return None

def _prep_hashtags_and_mentions(self, data_slot):
    text_elements = data_slot.get("textExtra", None)
    challenges = data_slot.get("challenges", None)

    hashtags_metadata = []
    mentions_list = []
    if text_elements is not None:
        for element in text_elements:
            mention = element.get("userId", None)
            if mention == None:
                # its a hashtag!
                hashtag_data = {}
                hashtag_data["name"] = element.get("hashtagName", None)
                hashtag_data["id"] = self._force_to_int(element.get("hashtagId", None))
                hashtag_data["type"] = element.get("type", None)
                hashtag_data["sub_type"] = element.get("subType", None)
                hashtag_data["is_commerce"] = element.get("isCommerce", None)

                matching_callenge = list(filter(lambda x : self._force_to_int(x["id"]) == hashtag_data["id"], challenges))
                if matching_callenge:
                    matching_callenge = matching_callenge[0]
                    hashtag_data["description"] = matching_callenge["desc"]
                else:
                    hashtag_data["description"] = None

                hashtags_metadata.append(hashtag_data)
            else:
                # its no hashtag!
                mentions_list.append(mention)
            
    return hashtags_metadata, mentions_list

def _filter_tiktok_data(self, data_slot):
    hashtags_metadata, mentions_list = self._prep_hashtags_and_mentions(data_slot)

    # video metadata
    video_metadata = {}
    ## id --> bigint NOT NULL
    video_metadata["id"] = self._force_to_int(data_slot.get("id", None)) #ID of the specific video
    ## time_created --> timestamp without time zone,
    video_metadata["time_created"] = datetime.fromtimestamp(int(data_slot.get("createTime", None))).isoformat()
    ## author_id --> bigint
    video_metadata["author_id"] = self._force_to_int(data_slot.get("author", {}).get("id", None))
    ## description --> text
    video_metadata["description"] = data_slot.get("desc", None)
    ## hashtags --> character varying(250)[]
    video_metadata["hashtags"] = [h['name'] for h in hashtags_metadata]
    ## mentions --> bigint[]
    if mentions_list:
        video_metadata["mentions"] = mentions_list # author ids of mentioned users
    else:
        video_metadata["mentions"] = None
    ## music_id --> bigint
    video_metadata["music_id"] = self._force_to_int(data_slot.get("music", {}).get("id", None))
    ## schedule_time --> integer
    video_metadata["schedule_time"] = data_slot.get("scheduleTime", None)
    ## location_created --> character varying(2)
    video_metadata["location_created"] = data_slot.get("locationCreated", None)

    if video_metadata["location_created"] and len(video_metadata["location_created"]) > 2:
        if video_metadata["location_created"] == "FAKE-AD":
            video_metadata["location_created"] = "XX"
        else:
            video_metadata["location_created"] = None
    ## is_ad --> boolean
    video_metadata["is_ad"] = data_slot.get("isAd", False) # Not in metadata seems to mean FALSE
    ## suggested_words --> character varying(250)[]
    video_metadata["suggested_words"] = data_slot.get("suggestedWords", None)
    if video_metadata["suggested_words"] and len(video_metadata["suggested_words"]) == 0:
        video_metadata["suggested_words"] = None

    ## statistics for video metadata
    try:
        stats_data = data_slot["statsV2"]
    except KeyError:
        stats_data = data_slot.get("stats", {})

    ## diggcount --> integer
    video_metadata["diggcount"] = self._force_to_int(stats_data.get("diggCount", None))
    ## sharecount --> integer
    video_metadata["sharecount"] = self._force_to_int(stats_data.get("shareCount", None))
    ## commentcount --> integer
    video_metadata["commentcount"] = self._force_to_int(stats_data.get("commentCount", None))
    ## playcount --> integer
    video_metadata["playcount"] = self._force_to_int(stats_data.get("playCount", None))
    ## collectcount --> integer
    video_metadata["collectcount"] = self._force_to_int(stats_data.get("collectCount", None))
    ## repostcount --> integer
    video_metadata["repostcount"] = self._force_to_int(stats_data.get("repostCount", None))

    ## poi data for video metadata
    poi_data = stats_data.get("poi", None)
    if poi_data is not None:
        ## poi_name --> character varying(250)
        video_metadata["poi_name"] = poi_data.get("name", None)
        ## poi_address --> character varying(250)
        video_metadata["poi_address"] = poi_data.get("address", None)
        ## poi_city --> character varying(250)
        video_metadata["poi_city"] = poi_data.get("city", None)

    ## warn_info --> json[]
    video_metadata["warn_info"] = data_slot.get("warnInfo", None)
    if video_metadata["warn_info"] == {}:
        video_metadata["warn_info"] = None
    ## original_item --> boolean
    video_metadata["original_item"] = data_slot.get("originalItem", None)
    ## offical_item --> boolean
    video_metadata["offical_item"] = data_slot.get("officalItem", None)
    ## secret --> boolean
    video_metadata["secret"] = data_slot.get("secret", None)
    ## for_friend --> boolean
    video_metadata["for_friend"] = data_slot.get("forFriend", None)
    ## digged --> boolean
    video_metadata["digged"] = data_slot.get("digged", None)
    ## item_comment_status --> smallint
    video_metadata["item_comment_status"] = data_slot.get("itemCommentStatus", None)
    ## take_down --> integer
    video_metadata["take_down"] = data_slot.get("takeDown", None)
    ## effect_stickers --> character varying(250)[]
    video_metadata["effect_stickers"] = data_slot.get("effectStickers", None)
    if len(video_metadata["effect_stickers"]) == 0:
        video_metadata["effect_stickers"] = None
    ## private_item --> boolean
    video_metadata["private_item"] = data_slot.get("privateItem", None)
    ## duet_enabled --> boolean
    video_metadata["duet_enabled"] = data_slot.get("duetEnabled", False) # Not in metadata seems to mean FALSE
    ## stitch_enabled --> boolean
    video_metadata["stitch_enabled"] = data_slot.get("stitchEnabled", False) # Not in metadata seems to mean FALSE
    ## stickers_on_item --> character varying(250)[]
    video_metadata["stickers_on_item"] = data_slot.get("stickersOnItem", None)
    if len(video_metadata["stickers_on_item"]) == 0:
        video_metadata["stickers_on_item"] = None
    ## share_enabled --> boolean
    video_metadata["share_enabled"] = data_slot.get("shareEnabled", None)
    ## comments --> character varying(250)[]
    video_metadata["comments"] = data_slot.get("comments", None)
    if len(video_metadata["comments"]) == 0:
        video_metadata["comments"] = None
    ## duet_display --> integer
    video_metadata["duet_display"] = data_slot.get("duetDisplay", None)
    ## stitch_display --> integer
    video_metadata["stitch_display"] = data_slot.get("stitchDisplay", None)
    ## index_enabled --> boolean
    video_metadata["index_enabled"] = data_slot.get("indexEnabled", False) # Not in metadata seems to mean FALSE
    ## diversification_labels --> character varying(250)[]
    video_metadata["diversification_labels"] = data_slot.get("diversificationLabels", None)
    if video_metadata["diversification_labels"] and len(video_metadata["diversification_labels"]) == 0:
        video_metadata["diversification_labels"] = None
    ## diversification_id --> bigint
    video_metadata["diversification_id"] = data_slot.get("diversificationId", None)
    ## channel_tags --> character varying(250)[]
    video_metadata["channel_tags"] = data_slot.get("channelTags", None) # wirklich dem Author zugehörig?
    if video_metadata["channel_tags"] == {}:
        video_metadata["channel_tags"] = None
    ## keyword_tags --> json[]
    video_metadata["keyword_tags"] = data_slot.get("keywordTags", None)
    ## is_ai_gc --> boolean
    video_metadata["is_ai_gc"] = data_slot.get("IsAigc", None)
    ## ai_gc_description --> text
    video_metadata["ai_gc_description"] = data_slot.get("AIGCDescription", None)
    if video_metadata["ai_gc_description"] == '':
        video_metadata["ai_gc_description"] = None

    # ---
    
    # Video Files metadata
    file_metadata = {}
    ## id --> bigint NOT NULL
    file_metadata["id"] = self._force_to_int(data_slot.get("id", None)) #ID of the specific video
    ## filepath --> path NOT NULL
    file_metadata["filepath"] = None #specified later
    ## duration --> integer
    file_metadata["duration"] = data_slot.get("video", {}).get("duration", None)
    ## height --> integer
    file_metadata["height"] = data_slot.get("video", {}).get("height", None)
    ## width --> integer
    file_metadata["width"] = data_slot.get("video", {}).get("width", None) 
    ## ratio --> integer
    file_metadata["ratio"] = data_slot.get("video", {}).get("ratio", None) #in p
    if file_metadata["ratio"]:
        file_metadata["ratio"] = self._force_to_int(file_metadata["ratio"][:-1]) # 540p -> 540
    else:
        file_metadata["ratio"] = None
    ## volume_loudness --> numeric(3, 1)
    file_metadata["volume_loudness"] = data_slot.get("video", {}).get("volumeInfo", {}).get("Loudness", None)
    ## volume_peak --> numeric(6, 5)
    file_metadata["volume_peak"] = data_slot.get("video", {}).get("volumeInfo", {}).get("Peak", None)
    ## has_original_audio --> boolean
    file_metadata["has_original_audio"] = data_slot.get("video", {}).get("claInfo", {}).get("hasOriginalAudio", None)
    ## enable_audio_caption --> boolean
    file_metadata["enable_audio_caption"] = data_slot.get("video", {}).get("claInfo", {}).get("enableAutoCaption", None)
    ## no_caption_reason --> smallint
    file_metadata["no_caption_reason"] = data_slot.get("video", {}).get("claInfo", {}).get("noCaptionReason", None)

    # ---

    # Video Music metadata
    music_metadata = {}
    ## id --> bigint
    music_metadata["id"] = video_metadata["music_id"] # ID of the music, not the video!
    ## title --> character varying(250)
    music_metadata["title"] = data_slot.get("music", {}).get("title", None)
    if music_metadata["title"]:
        if len(music_metadata["title"]) > 250:
            music_metadata["title"] = music_metadata["title"][:250]
    ## author_name --> character varying(250)
    music_metadata["author_name"] = data_slot.get("music", {}).get("authorName", None)
    if music_metadata["author_name"]:
        if len(music_metadata["author_name"]) > 250:
            music_metadata["author_name"] = music_metadata["author_name"][:250]

    ## original --> boolean
    music_metadata["original"] = data_slot.get("music", {}).get("original", None)
    ## schedule_search_time --> integer
    music_metadata["schedule_search_time"] = data_slot.get("music", {}).get("scheduleSearchTime", None)
    ## collected --> boolean
    music_metadata["collected"] = data_slot.get("music", {}).get("collected", None)
    ## precise_duration --> json
    music_metadata["precise_duration"] = data_slot.get("music", {}).get("preciseDuration", None)

    # ---

    # Author metadata
    author_metadata = {}
    ## id --> bigint
    author_metadata["id"] = self._force_to_int(data_slot.get("author", {}).get("id", None))
    ## username --> character varying(250)
    author_metadata["username"] = data_slot.get("author", {}).get("uniqueId", None)
    ## name --> character varying(250)
    author_metadata["name"] = data_slot.get("author", {}).get("nickname", None)
    ## signature --> text
    author_metadata["signature"] = data_slot.get("author", {}).get("signature", None)
    ## create_time --> integer
    author_metadata["create_time"] = data_slot.get("author", {}).get("createTime", None)
    ## verified --> boolean
    author_metadata["verified"] = data_slot.get("author", {}).get("verified", None)
    ## ftc --> boolean
    author_metadata["ftc"] = data_slot.get("author", {}).get("ftc", None)
    ## relation --> integer
    author_metadata["relation"] = data_slot.get("author", {}).get("relation", None)
    ## open_favorite --> boolean
    author_metadata["open_favorite"] = data_slot.get("author", {}).get("openFavorite", None)
    ## comment_setting --> integer
    author_metadata["comment_setting"] = data_slot.get("author", {}).get("commentSetting", None)
    ## duet_setting --> smallint
    author_metadata["duet_setting"] = data_slot.get("author", {}).get("duetSetting", None)
    ## stitch_setting --> smallint
    author_metadata["stitch_setting"] = data_slot.get("author", {}).get("stitchSetting", None)
    ## private_account --> boolean
    author_metadata["private_account"] = data_slot.get("author", {}).get("privateAccount", None)
    ## secret --> boolean
    author_metadata["secret"] = data_slot.get("author", {}).get("secret", None)
    ## is_ad_virtual --> boolean
    author_metadata["is_ad_virtual"] = data_slot.get("author", {}).get("isADVirtual", None)
    ## download_setting --> smallint
    author_metadata["download_setting"] = data_slot.get("author", {}).get("downloadSetting", None)
    ## recommend_reason --> character varying(250)
    author_metadata["recommend_reason"] = data_slot.get("author", {}).get("recommendReason", None)
    ## suggest_account_bind --> boolean
    author_metadata["suggest_account_bind"] = data_slot.get("author", {}).get("suggestAccountBind", None)

    # ---x

    # combine all
    filtered_metadata = {}
    filtered_metadata["video_metadata"] = video_metadata
    filtered_metadata["file_metadata"] = file_metadata
    filtered_metadata["music_metadata"] = music_metadata
    filtered_metadata["author_metadata"] = author_metadata
    filtered_metadata["hashtags_metadata"]= hashtags_metadata

    return filtered_metadata
