#!/usr/bin/env python
import ConfigParser
import datetime
import urllib, json
import sqlite3
import sys
from email.mime.text import MIMEText
from subprocess import Popen, PIPE

config = ConfigParser.RawConfigParser()
cfgfile = sys.argv[1]

config.read(cfgfile)
dir = config.get('Global', 'dir')
apikey = config.get('Global', 'apikey')
fromaddr = config.get('Global', 'fromaddr')

domain = sys.argv[2]
mailto = sys.argv[3]

#connect to DB - create one if it does not exist
conn = sqlite3.connect(dir+'/dbs/cmddb-'+domain+'.db')
c = conn.cursor()

# Create table if not exists
c.execute('''CREATE TABLE if not exists creds
             (username text, password text, userbase text, dump_date text)''')

conn.commit()

#reset the variables
msgstring=""
newcounter=0
counter=0

#retrieve the dumps from Ryans dump service
url="https://checkmydump.miscreantpunchers.net/api/domain/"+domain+"?key="+apikey
response = urllib.urlopen(url)
data = json.loads(response.read())


#go through the results(rows) and work out what is new
try:
	for row in data['rows']:
		#try to find if we have seen this entry before
		c.execute("SELECT * FROM creds where username=? and password=? and userbase=? and dump_date=?", (row['username'], row['password'], row['userbase'], row['dump_date']))
		conn.commit()
		counter+=1
		#if we didnt find this entry in the database, enter it and build a string for the email notification
		if len(c.fetchall()) == 0:
			c.execute("INSERT into creds (username, password, userbase, dump_date) VALUES (?,?,?,?)", (row['username'], row['password'], row['userbase'], row['dump_date']))
		        #conn.commit()
			newstring = "DUMP DATE:"+row['dump_date']+", USERBASE: "+row['userbase']+", USER: "+row['username']+", PASSWORD: "+row['password']+"\r\n"
			msgstring += newstring
			newcounter+=1
except KeyError:
	#none found
	error=1
except:
	logfile.write("Unexpected error:", sys.exec_info()[0])
	print("Unexpected error:", sys.exec_info()[0])

#email the new results
if newcounter > 0:
	msg = MIMEText(msgstring)
	msg["From"] = fromaddr
	msg["To"] = mailto
	msg["Subject"] = "CMD New Credentials for "+domain
	p = Popen(["/usr/sbin/sendmail", "-t", "-oi"], stdin=PIPE)
	p.communicate(msg.as_string())	
	
with open(dir+"/logs/cmd-"+domain+".log", "a+") as logfile:
	logfile.write(str(datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))+" CheckMyDump - "+str(counter)+" entries found for "+domain+", "+str(newcounter)+" new\n\r")

#print(str(datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))+" CheckMyDump - "+str(counter)+" entries found for "+domain+", "+str(newcounter)+" new")

conn.close()
