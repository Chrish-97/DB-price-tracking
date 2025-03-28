Ticket Price Tracking App

This Python application allows you to regularly track ticket prices for Deutsche Bahn (DB) train routes and sends notifications when the price drops. It helps users keep an eye on ticket prices and make timely decisions to book tickets at the best rates.
  1. Create and activate a Python environment in the project folder:  
   ```python3 -m venv venv```  
   ```source venv/bin/activate```  
  2.	Install dependencies:  
   ```pip install -r requirements.txt```  
  3.	Create a cron job that also logs output to a .txt file:  
   ```crontab -e```  
  ```source /path/to/your/project/venv/bin/activate && python /path/to/your/project/ticket.py >> /path/to/your/project/log.txt 2>&1```  
  Press ESC and type :wq to save and exit (mac)  
  4.	Manually run the cron job:  
   ```/usr/bin/caffeinate -i /bin/bash -c 'source /path/to/your/project/venv/bin/activate && python /path/to/your/project/ticket.py >> /path/to/your/project/log.txt 2>&1'```    
  5.	Twilio Notifications Setup:  
  The notification feature with Twilio will only work if you create a free Twilio account first. Once your account is set up, create a sandbox in the Twilio console, and then insert the Auth Token into the ```send_notifications`` function for it to work.

  
  
