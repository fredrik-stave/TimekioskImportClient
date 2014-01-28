#
# timekiosk.py
#
# @author Fredrik Stave <fredrik@webokonomi.no>
# @version 1.0.0
# @since 27.01.2014
#
# Copyright (C) 2014 Fredrik Stave
# THIS PROGRAM COMES WITH ABSOLUTELY NO WARRANTY
# THIS IS FREE SOFTWARE, AND YOU ARE WELCOME TO REDISTRIBUTE IT
# UNDER CERTAIN CONDITIONS; SEE 'LICENCE' FOR DETAILS OR
# SEE <http://heim.ifi.uio.no/fredrls/license/gnu-gpl/LICENSE>
#

"""
This is the Timekiosk Import Client program.
It's main purpose is to fetch files from Timekiosk, and then uploading them to Xledger.
The program is dependant upon several other services, see the 'DEPENDENCIES' file for a list of these dependencies.
To use the program, siply run it from the command line using 'python Timekiosk_import_clien.py run'.
There are numerous options for running the program, and several ways of setting up the configurations.
For more information on these topics, please consult 'INSTALL' and 'README' files where the installation process and
runtime behaviour is outlined.
"""
class timekiosk(object):
	# class variables
	pos_dict = {}
	
	"""
	This function constructs the class and fetches the options from the config file if it exists.
	If not, the program defaults to static options. These will be relative to the current working directory.
	"""
	def __init__(self):
		import csv, re, os
		self.settings = {}
		if os.path.isfile("config/config.csv"):
			config = os.path.abspath("config/config.csv")
			with open(config, 'rb') as settings_file:
				config_contents = csv.reader(settings_file, delimiter=';')
				for row in config_contents:
					self.settings[row[0]] = self.format_option(row[1])
		else:
			self.settings['name'] = 'Timekiosk Import Client'
			self.settings['version'] = '1.0'
			self.settings['pos_dir'] = 'pos/'
			self.settings['pos_file'] = 'pos.csv'
			self.settings['asset_dir'] = 'assets/'
			self.settings['error_dir'] = 'error/'
			self.settings['temp_dir'] = 'temp/'
			self.settings['mail_response_active'] = False
			self.settings['mail_server_recipients'] = None
			self.settings['mail_server_sender'] = None
			self.settings['mail_server'] = None
			self.settings['mail_server_port'] = None
			self.settings['mail_server_username'] = None
			self.settings['mail_server_password'] = None

	def init_recon(self):
		# this method runs the whole thing.
		process_pos_dir()
		for id in pos_dict.keys():
			new_recon_no = self.pos_dict[id] + 1
			no_error = True
			while no_error:
				# this next line of code shall ask the fetch_file function to do all the filehandling
				# and similar actions and just return the message and exit/response code given by the AutomationClient.exe
				response = self.fetch_file(new_recon_no, id)
				
				# Error codes:
				# 0 - OK
				# 1 - Config filepath argument missing (a) - Aborting.
				# 5 - Unable to find or load config file - Aborting.
				# 100 - No transactions present - Aborting. Level 0
				# 100 - Posterminal ID not allowed - Aborting. Level 1
				# 100 - Multiple VAT rates discovered for product sales on the same account reference (3000) - Aborting. Level 2
				# WindowsError: [Error 2] The system cannot find the file specified
				
				if response['exit_code'] == '0':
					new_recon_no+=1
				elif response['exit_code'] == '100':
					if response['error_level'] == '0':
						no_error = False
					else:
						# send the error message to the administrator if allowed
						new_recon_no-=1
						no_error = False
						print "an appropriate error message when the pos id is not allowed"
				elif response['exit_code'] == '1':
					# send the error message to the administrator if allowed
					new_recon_no-=1
					no_error = False
					print "an appropriate error message when the pos id is not allowed"
				# Other response codes if any
				elif response['exit_code'] == '5':
					# send the error message to the administrator if allowed
					new_recon_no-=1
					no_error = False
					print "an appropriate error message when the pos id is not allowed"
				elif response['exit_code'] == 'WindowsError':
					# send the error message to the administrator if allowed
					new_recon_no-=1
					no_error = False
					print "an appropriate error message when the pos id is not allowed"
				else:
					# send the error message to the administrator if allowed
					new_recon_no-=1
					print "[Error]: an unknown error occured when retrieving the recon file with recon no. %s for pos id %s." % (str(new_recon_no), id)
					no_error = False
			self.pos_dict[id] = new_recon_no

	"""
	This function processes the pos file in the pos directory, then adds the files to the pos dictionary.
	"""
	def process_pos_dir(self):
		# Fetching:
		# import subprocess
		# command = ['C://TKA_SmallSize/bin/AutomationClient.exe', '/config=C:\\\\TKA_SmallSize\\config\\XLedgerRecon.xml', 'ReconNo=1', 'PosId=173']
		# process = subprocess.Popen(command, shell=True)
		# Check if it's possible to ommit the shell=True argument to suppress the output.
		import os, csv
		raw_pos_file = self.settings['pos_dir']+'/'+self.settings['pos_file']
		if os.path.isfile(raw_pos_file):
			with open(raw_pos_file, 'rb') as pos_file:
				pos_content = csv.reader(pos_file, delimiter=':')
				for pos_id in pos_content:
					pos_dict[pos_id[0]] = int(pos_id[1])

	"""
	Fetches the files
	"""
	def fetch_file(self, recon_no, pos_id):
		client = self.settings['client_path']
		config = self.settings['client_config']
		recon = 'ReconNo=%s' % recon_no
		pos = 'PosId=%s' % str(pos_id)
		command = list(client, config, recon, pos)
		process = subprocess.Popen(command, shell=False)
		
		# TODO: do some processing
		# send to parse_response()
		response = self.parse_response(process)
		
		if self.is_valid_response(response):
			# move files to the export directory and return the formatted response dictionary
			pass
		else:
			# return the formatted response dictionary
			pass
		pass
	
	"""
	This function parses the raw response output from the AutomationClient.exe program and formats it to a
	key-value based dictionary on a standardized format defined in the documentation.
	"""
	def parse_response(self, raw_response):
		import re
		response = {}
		
		target_filepath_pattern = r'/^target *filepath: *(.+)$/'
		server_response_status_pattern = r'/^server *response *status: *(.+)$/'
		special_case_server_response_pattern = r'/^server *response *status: *.*posterminal id not allowed.*$/'
		exit_code_pattern = r'/^exit *code: *(.+)$/'

		target_filepath = re.search(target_filepath_pattern, raw_response, flags=re.I)
		server_response_status = re.search(server_response_status_pattern, raw_response, flags=re.I)
		exit_code = re.search(exit_code_pattern, raw_response, flags=re.I)

		if target_filepath:
			response['target_filepath'] = target_filepath.group(1)
		else:
			response['target_filepath'] = ''
		if server_response_status:
			response['server_response_status'] = server_response_status.group(1)
		else:
			response['server_response_status'] = ''
		if re.match(special_case_server_response_pattern, raw_response, flags=re.I):
			response['exit_code'] = 101
		elif exit_code:
			response['exit_code'] = int(exit_code.group(1))
		else:
			response['exit_code'] = -1

		return response


	def is_valid_response(self, response):
		return response['exit_code'] == 0

	"""
	This function casts the option values to the correct type based on the value.
	"""
	def format_option(self, value):
		import re
		true_pattern = r'true|yes'
		false_pattern = r'false|no'
		float_pattern = r'/\d*\.\d+|\d+\.\d*'
		integer_pattern = r'^\d+$'
		array_pattern = r'/\[(.+\, *)+]|(.+, *)+|\{(.+\, *)+}/'
	
		if re.match(true_pattern, value, flags=re.I):
			return True
		if re.match(false_pattern, value, flags=re.I):
			return False
		if re.match(float_pattern, value):
			return float(value)
		if re.match(integer_pattern, value):
			return int(value)
		if re.match(array_pattern, value, re.I):
			value=re.sub(r'[\[\{\]\}]','',value)
			return re.split(r', *', value)
		if value=='':
			return None
		return value

	"""
	This function takes an error code and an optional filename as arguments, and based on those
	sends an error e-mail message to the recipients defined in the config file.
	"""
	def error_message(self, error_code, filename=None):
		if self.settings['mail_response_active']:
			import re, smtplib, email, email.encoders, email.mime.text, email.mime.base
			from time import localtime, strftime

			mail_server = self.settings['mail_server']
			mail_server_port = self.settings['mail_server_port']
			mail_server_username = self.settings['mail_server_username']
			mail_server_password = self.settings['mail_server_password']
			mail_server_sender = self.settings['mail_server_sender']
			smtpserver = smtplib.SMTP(mail_server, mail_server_port)
			smtpserver.ehlo()
			smtpserver.starttls()
			smtpserver.ehlo
			smtpserver.login(mail_server_username, mail_server_password)

			FROM = '%s <%s>' % (self.settings['name'], mail_server_sender)
			TO = self.settings['mail_server_recipients']
			SUBJECT = '[Feil #%s]: Feil ved import av Timekiosk filer' % error_code
			MESSAGE = ""
			if filename != None:
				MESSAGE += """
Dato: %s
Feilkode: %s
Filnavn: %s

Det oppstod en feil ved import av fil til Xledger.
Filen er overf&#248;rt til mappen <b>%s</b>.
For &#229; h&#229;ndtere denne filen manuelt, sl&#229; opp feilkoden i dokumentasjonen og
endre filen slik at denne feilen blir rettet opp. Deretter last den manuelt opp til Xledger.
Vedlagt denne meldingen finner du en kopi av filen som inneholdt feil.

Denne meldingen ble generert automatisk av %s.
				""" % (strftime("%Y-%m-%d %H:%M:%S", localtime()), error_code, filename, self.settings['error_dir'], self.settings['name'])
			else:
				MESSAGE += """
Dato: %s
Feilkode: %s

Det oppstod en feil ved import av fil til Xledger.
Det er uklart hva som har skjedd med filen. For &#229; feils&#248;ke problemet,
g&#229; til mappen %s.

Denne meldingen ble generert automatisk av %s.
				""" % (strftime("%Y-%m-%d %H:%M:%S", localtime()), error_code, self.settings['error_dir'], self.settings['name'])
	
			# Creating the HTML e-mail
			html = '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" '
			html += '"http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd"><html xmlns="http://www.w3.org/1999/xhtml">'
			html += '<body><pre>%s</pre>' % MESSAGE
			html += '</body></html>'

			emailMsg = email.MIMEMultipart.MIMEMultipart('mixed')
			emailMsg['Subject'] = SUBJECT
			emailMsg['From'] = FROM
			emailMsg['To'] = ', '.join(TO)
			emailMsg.attach(email.mime.text.MIMEText(html,'html'))

			# Attach a file if present
			if filename != None:
				fileMsg = email.mime.base.MIMEBase('application','octet-stream')
				fileMsg.set_payload(open(filename, 'rb').read())
				email.encoders.encode_base64(fileMsg)
				fileMsg.add_header('Content-Disposition','attachment;filename='+os.path.basename(filename))
				emailMsg.attach(fileMsg)
	
			smtpserver.sendmail(mail_server_sender, TO, emailMsg.as_string())
			smtpserver.close()
		else:
			# write to the log file


print timekiosk().process_pos_dir()
