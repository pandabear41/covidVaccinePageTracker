import secrets
from bs4 import BeautifulSoup
import urllib3, re, sched, time, dateparser, logging, datetime, sys
from notifiers import get_notifier

file_handler = logging.FileHandler(filename='tracker.log')
stdout_handler = logging.StreamHandler(sys.stdout)
handlers = [file_handler, stdout_handler]
logging.basicConfig(encoding='utf-8', level=logging.DEBUG, format="%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s", handlers=handlers)

p = get_notifier('pushover')
s = sched.scheduler(time.time, time.sleep)

def scheduleRun():
    logging.debug("Sleeping %d seconds", secrets.delay)
    s.enter(secrets.delay, 1, checkSite)
    s.run()

def checkSite():
    logging.debug("Checking page")
    try:
        req = urllib3.PoolManager()
        page = req.request('GET', secrets.url)
    except:
        logging.error("Unable to request URL: %s", secrets.url)
        scheduleRun()
        return

    try:
        soup = BeautifulSoup(page.data, 'html.parser')
    except:
        logging.error("Soup unable to parse html, %s", page.data)
        scheduleRun()
        return

    try:
        sectionsSpots = soup.find_all(class_= 'spots-remaining')
    except:
        logging.error("Soup unable to parse sections.")
        scheduleRun()
        return

    count = 0
    gMessage = ""
    perr = False
    for section in sectionsSpots:
        if section.text != '0':
            count += 1
            logging.debug("Found a spot.")
            try:
                rootSection = section.parent.parent.parent.parent
                sDateSection = rootSection.find_all(class_= 'startDate')
                eDateSection = rootSection.find_all(class_= 'endDate')
                if sDateSection.len() >= 1:
                    sDate = dateparser.parse(sDateSection[0], settings={'TIMEZONE': 'America/Phoenix'})
                if eDateSection.len() >= 1:
                    eDate = dateparser.parse(sDateSection[0], settings={'TIMEZONE': 'America/Phoenix'})
                
                tMessage = f"{section.text} spots on {sDate.strftime('%m/%d')} from {sDate.strftime('%I:%M%p')} to {eDate.strftime('%I:%M%p')}"
                logging.debug(tMessage)
                gMessage += tMessage + "\n"
            except:
                logging.error("Unable to parse section, fallback send alert anyway with no data.")
                perr = True

    if count > 0:
        if perr:
            gMessage += "Sections available, but can't find section data.\n"      
        # if gMessage == "":
        #     gMessage = "Nothing to report"
        poTitle = f"{count} sections available"
        logging.debug("Sent pushover message")
        p.notify(message=gMessage, title=poTitle, token=secrets.poApp, user=secrets.poUser, sound=secrets.poSound, priority=secrets.poPriority)
        logging.debug("Sleeping %d seconds", secrets.poThrottleSecs)
        s.enter(secrets.poThrottleSecs, 1, checkSite)
        s.run()
        return
    
    scheduleRun()

logging.debug("Program start")
checkSite()            


