from stem import Signal
from stem.control import Controller
import requests
#import youtube_dl
import yt_dlp
import os
import sys
import time
import glob
import logging

from tor_scraper.base_scraper import Scraper


class YoutubeTOAST(Scraper):
    """Tor-Operated Audio Scraping Tool for Youtube"""
    def __init__(self, wait_time = 0.35, output_files_fp = "data/", progress_file_fn = "scraping_progress.json", logger = None):
        super().__init__(wait_time, output_files_fp, progress_file_fn, logger)

    def delete_non_mp3_files(self, directory):
        """Delete all files that are not .mp3 in the specified directory"""
        
        if not os.path.exists(directory):
            print(f"Directory '{directory}' does not exist")
            return
        
        # Get all files in directory
        all_files = glob.glob(os.path.join(directory, "*"))

        print(all_files)
        user_input = input('Would you like to delete these files (y/n)?')

        if user_input.lower() == 'yes':
            print('user typed yes')
            deleted_count = 0
            for file_path in all_files:
                # Check if it's a file (not a subdirectory) and not .mp3
                if os.path.isfile(file_path) and not file_path.lower().endswith('.mp3'):
                    os.remove(file_path)
                    deleted_count += 1
        
            print(f"Deleted {deleted_count} non-MP3 files")

        elif user_input.lower() == 'no':
            print('user typed no - nothing happens')
        else:
            print('Type yes or no - re-run please')        

    def renew_connection(self):
        """Signal Tor to create new connection"""
        with Controller.from_port(port = 9051) as controller:
            controller.authenticate(password="trtr2003!")
            controller.signal(Signal.NEWNYM)

    def get_tor_session(self):
        """Create a tor session"""
        session = requests.session()
        # Tor uses the 9050 port as the default socks port
        session.proxies = {'http':  'socks5://127.0.0.1:9050',
                        'https': 'socks5://127.0.0.1:9050'}
        return session

    def detailed_connection_test(self, url):
        """
        Tests the connection quality and response time to a specified URL through a Tor proxy connection. This function performs a comprehensive analysis of the network connection by making an HTTP GET request and measuring various performance metrics.
        
        Parameters
            url (str): The target URL to test the connection against. Must be a valid HTTP or HTTPS URL (e.g., "https://www.example.com"). The function will attempt to connect to this URL through the Tor network.

        Returns
        Returns a dictionary containing connection test results with the following structure:

        On Success:
            success (bool): Always True for successful connections
            response_time (float): Total response time in milliseconds from request initiation to completion
            status_code (int): HTTP status code returned by the server (e.g., 200, 404, 500)
            content_length (int): Size of the response content in bytes

        On Failure:
            success (bool): Always False for failed connections
            error (str): Error type description - one of:
                "Timeout": Request exceeded the 10-second timeout limit
                "Connection Error": Unable to establish connection to the target URL
                "[specific error message]": Other request-related errors with detailed description
        """
        try:
            # Custom headers to mimic a real browser
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
                    
            # Measure different aspects
            start_time = time.time()
            response = self.get_tor_session().get(url, headers=headers, timeout=10)
            total_time = time.time() - start_time
            
            # Get timing information
            #print(f"Status Code: {response.status_code}")
            #print(f"Total Time: {total_time * 1000:.2f} ms")
            #print(f"Content Length: {len(response.content)} bytes")
                    
            return {
                'success': True,
                'response_time': total_time * 1000,
                'status_code': response.status_code,
                'content_length': len(response.content)
            }
            
        except requests.exceptions.Timeout:
            print(f"Timeout: {url} took too long to respond")
            return {'success': False, 'error': 'Timeout'}
        
        except requests.exceptions.ConnectionError:
            print(f"Connection Error: Unable to connect to {url}")
            return {'success': False, 'error': 'Connection Error'}
        
        except requests.exceptions.RequestException as e:
            print(f"Request Error: {e}")
            return {'success': False, 'error': str(e)}
        
    def establish_tor_connection(self, max_response_time=5000, max_connection_retries=3, sleep_time=1, connection_established = False):
        """
        Establish a quality Tor connection with retry logic
        
        Parameters:
            max_response_time: Maximum acceptable response time in milliseconds (default: 5000ms)
            max_connection_retries: Maximum retries for connection issues (default: 3)
            sleep_time: Sleep time between connection activities (default: 1 second)
        
        Returns:
            bool: True if connection established successfully, False otherwise
        """
        connection_retries = 0
        
        while not connection_established and connection_retries < max_connection_retries:
            print(f"\n\n\nTesting connection... (attempt {connection_retries + 1}/{max_connection_retries})")
            
            test_results = self.detailed_connection_test("https://youtube.com")
            print(f"Connection time: {test_results.get('response_time', float('inf')):.2f} ms")
            
            if (test_results.get("success") and 
                test_results.get("status_code") == 200 and 
                test_results.get("response_time", float('inf')) < max_response_time):
                
                connection_established = True
                print(f"✓ Connection quality acceptable: {test_results['response_time']:.2f}ms")
                
            else:
                connection_retries += 1
                if connection_retries < max_connection_retries:
                    #print(f"✗ Connection quality poor or failed. Renewing Tor connection...")
                    try:
                        self.renew_connection()
                        #print(f"Tor connection renewed. Waiting {sleep_time} seconds...")
                        time.sleep(sleep_time/4)  # Wait for new connection to establish
                    except Exception as e:
                        print(f"Error renewing Tor connection: {e}")
                else:
                    print(f"✗ Failed to establish good connection after {max_connection_retries} attempts")
        
        return connection_established

    def download_video(self, videoId):
        """Downloads the audio of a youtube video using a tor session. 
        inspired by: https://github.com/garbit/youtube-downloader-over-tor/blob/master/downloader.py"""
        ydl_opts = {
            'format': 'worstaudio*',     # instead of 'bestaudio/best',
            'verbose': False,
            'quiet': True,
            'no_warnings': True,
            'user-agent': "Mozilla/5.0 (X11; Linux x86_64; rv:140.0) Gecko/20100101 Firefox/140.0",
            'outtmpl': self.output_files_fp + '%(id)s.%(ext)s',
            'proxy': 'socks5://127.0.0.1:9050',
            'nocheckcertificate': True,
            'sleep_interval': 0,
            'skip_unavailable_fragments':False, # dont know if works
            'abort-on-error':True,  # dont know if works
            'ignoreerrors':False,   # dont know if works
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([f'http://www.youtube.com/watch?v={videoId}'])    

    def download_videos_via_tor(self, max_response_time=5000, max_connection_retries=3, max_download_retries=2, sleep_time = 1):
        """
        Download videos via Tor with connection testing and error handling
        
        Parameters:
            post_ids: List of YouTube video IDs to download
            max_response_time: Maximum acceptable response time in milliseconds (default: 5000ms)
            max_connection_retries: Maximum retries for connection issues (default: 3)
            max_download_retries: Maximum retries for download failures (default: 2)
            sleep_time: Sleep time between various connection activities (default: 1 second)
        """

        post_ids = self.get_pending_objects()
        assert len(post_ids) > 0, "No more ids to scrape"
        successful_downloads = [] # counting only this session
        failed_downloads = [] # counting only this session
        
        print(f"Starting download of {len(post_ids)} videos via Tor...")
        print(f"Connection threshold: {max_response_time}ms")
        print("-" * 60)
        
        connection_established = False
        for i, post_id in enumerate(post_ids, 1):
            print(f"\n[{i}/{len(post_ids)}] Processing video: {post_id}")
            

            # Establish connection quality
            if not connection_established:
                connection_established = self.establish_tor_connection(
                    max_response_time=max_response_time,
                    max_connection_retries=max_connection_retries,
                    sleep_time=sleep_time
                )

            # Error if no connection available
            assert connection_established, "No connection possible"


            # Attempt to download video with retries
            download_successful = False
            download_retries = 0
            
            while not download_successful and download_retries < max_download_retries:
                try:
                    print(f"\n\n\nDownloading video... (attempt {download_retries + 1}/{max_download_retries})")
                    self.download_video(post_id)
                    download_successful = True
                    successful_downloads.append(post_id)
                    print(f"✓ Successfully downloaded: {post_id}")
                    print("-" * 60)
                    self.mark_completed(post_id, self.output_files_fp + f'{post_id}.mp3')
                    
                    # Brief pause between downloads to be respectful
                    time.sleep(sleep_time)
                    
                except Exception as e:
                    download_retries += 1
                    error_msg = str(e)
                    
                    print(f"✗ Download failed: {error_msg}")
                    
                    if download_retries < max_download_retries:
                        print(f"Retrying download... (attempt {download_retries + 1}/{max_download_retries})")
                        
                        try:
                            # Establish new quality connection to tor
                            self.renew_connection()
                            connection_established = self.establish_tor_connection(
                                max_response_time=max_response_time,
                                max_connection_retries=max_connection_retries,
                                sleep_time=sleep_time
                            )
                        except Exception as renewal_error:
                            print(f"Error renewing Tor connection: {renewal_error}")
                        
                        time.sleep(sleep_time/2)  # Brief pause before retry
                    else:
                        self.mark_error(post_id, error_msg)
                        failed_downloads.append({
                            'video_id': post_id,
                            'error': error_msg,
                            'attempts': download_retries
                        })
        
        # Print summary
        print("\n" + "=" * 60)
        print("DOWNLOAD SUMMARY")
        print("=" * 60)
        print(f"Total videos processed: {len(post_ids)}")
        print(f"Successful downloads: {len(successful_downloads)}")
        print(f"Failed downloads: {len(failed_downloads)}")
        
        if successful_downloads:
            print(f"\n✓ Successfully downloaded:")
            for video_id in successful_downloads:
                print(f"  - {video_id}")
        
        if failed_downloads:
            print(f"\n✗ Failed downloads:")
            for failure in failed_downloads:
                print(f"  - {failure['video_id']}: {failure['error']} (attempts: {failure['attempts']})")
        
        return {
            'successful': successful_downloads,
            'failed': failed_downloads,
            'total_processed': len(post_ids)
        }        

if __name__ == "__main__":
    MODE = "SCRAPE" # INIT or SCRAPE or CLEANUP or STATS

    if sys.argv[1]:
        MODE = sys.argv[1]

    if MODE == "INIT":
        # initial creation of seedlist / scraping_progress.json
        import re
        from tqdm import tqdm
        
        # Data Directory (without folder)
        output_files_fp = "/hdd1/youtube_data/"
        
        already_scraped_ids = glob.glob(f"{output_files_fp}audios/*.mp3", recursive=True)
        already_scraped_ids = [re.findall(r'.*/(.*).mp3', filename)[0] for filename in already_scraped_ids]
        already_scraped_ids = set(already_scraped_ids)
        
        to_be_scraped_ids = glob.glob(f"{output_files_fp}posts/*.json", recursive=True)
        to_be_scraped_ids = [re.findall(r'.*/(.*).json', filename)[0] for filename in to_be_scraped_ids]
        to_be_scraped_ids = set(to_be_scraped_ids)
        print(len(to_be_scraped_ids))
        
        toast = YoutubeTOAST()
        toast.load_state() # creating new state
        toast.add_objects(to_be_scraped_ids)
        filepaths = [output_files_fp + f'audios/{id}.mp3' for id in already_scraped_ids]
        toast.mark_completed_multi(list(already_scraped_ids), filepaths)
    
    elif MODE == "SCRAPE":
        # Data Directory
        output_files_fp = "/hdd1/youtube_data/audios/"
        
        toast = YoutubeTOAST(
                        wait_time = 0.35,
                        output_files_fp = output_files_fp,
                        progress_file_fn = "scraping_progress.json",
                        logger = None
                    )
        toast.load_state()
        print(toast.get_stats())

        results = toast.download_videos_via_tor(
            max_response_time=1100,  # 1 second = 1000ms
            max_connection_retries=50,
            max_download_retries=3,
            sleep_time=1 # in seconds
        )
    
    elif MODE == "CLEANUP":
        toast = YoutubeTOAST()
        output_files_fp = "/hdd1/youtube_data/audios/"
        toast.delete_non_mp3_files(output_files_fp)
    
    elif MODE == "STATS":
        toast = YoutubeTOAST()
        print(toast.get_stats())


# 22.07 19:10 -> pending 317.104
# 23.07 12:36 -> pending 316.438
# => 38 videos per hour
# 24.07 12:38 -> pending 315.666
# 25.07 15:42 -> pending 314.832
# # => 30 videos per hour
