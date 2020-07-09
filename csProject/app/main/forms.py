from flask_wtf import FlaskForm
from wtforms import StringField, RadioField, DateField, IntegerField
from wtforms.validators import InputRequired, ValidationError, URL
import validators
from datetime import date

def valid_urls(url_list):
	for url in url_list:
		if not validators.url(url.strip()):
			return False
	return True
	
class RepoURLForm(FlaskForm):
	''' used for statistics page '''
	url = StringField('url', validators=[InputRequired("Please provide a repository URL."), URL(message="Invalid URL")])
	view = StringField('view', default='raw')

	def validate_on_submit(self):
		result = super(RepoURLForm, self).validate()
		return result

class RepoURLArchiveForm(FlaskForm):
	''' used for one or few repo urls on home page '''
	url = StringField('url', validators=[InputRequired(message="Please fill out all fields."), URL(message="Invalid URL")])
	start_date = DateField(id='start_date', format='%d/%m/%Y', validators=[InputRequired(message="Please fill out all fields.")])
	end_date = DateField(id='end_date', format='%d/%m/%Y', validators=[InputRequired(message="Please fill out all fields.")])

	def validate_on_submit(self):
		result = super(RepoURLArchiveForm, self).validate()
		if not result:
			return False

		if not validators.url(self.url.data):
			RepoURLArchiveForm.errors = {'url':'Invalid URL'}
			return False

		if (self.start_date.data > self.end_date.data):
			RepoURLArchiveForm.errors = {'start_date':'\'To\' date must be after \'From\' date.'}
			return False
		else:
			return result

class RepoURLArchiveFormCSV(FlaskForm):
	''' used for multiple url input on home page '''
	urls = StringField('urls', validators=[InputRequired(message="Please fill out all fields.")])
	start_date = DateField(id='start_date', format='%d/%m/%Y', validators=[InputRequired(message="Please fill out all fields.")])
	end_date = DateField(id='end_date', format='%d/%m/%Y', validators=[InputRequired(message="Please fill out all fields.")])

	def validate_on_submit(self):
		result = super(RepoURLArchiveFormCSV, self).validate()
		if not result:
			return False

		url_list = self.urls.data.split(',')
		for url in url_list:
			if not validators.url(url):
				RepoURLArchiveFormCSV.errors = {'url':'Invalid URL'}
				return False

		if (self.start_date.data > self.end_date.data):
			RepoURLArchiveFormCSV.errors = {'start_date':'\'To\' date must be after \'From\' date.'}
			return False
		else:
			return result

	def get_csv_urls(self):
		''' Remove whitespace from comma separated values and return as list '''
		return [url.strip() for url in self.urls.data.split(',')]

class ChangeLanguageForm(FlaskForm):
	''' allows user to change linguist language '''
	language = StringField('language', validators=[InputRequired()])

class FiltersForm(FlaskForm):
	''' allows user to change the search criteria for the discover route '''
	language = StringField('language', validators=[InputRequired(message="Please fill out all fields.")])
	created_before = DateField(id='created_before', format='%Y-%m-%d', validators=[InputRequired(message="Please fill out all fields.")])
	updated_after = DateField(id='pushed_after', format='%Y-%m-%d', validators=[InputRequired(message="Please fill out all fields.")])
	min_size = IntegerField('min_size', validators=[InputRequired(message="Please fill out all fields.")])
	max_size = IntegerField('max_size', validators=[InputRequired(message="Please fill out all fields.")])


	def validate_on_submit(self):
		result = super(FiltersForm, self).validate()
		if not result:
			return False

		if (int(self.max_size.data) < int(self.min_size.data)):
			FiltersForm.errors = {'min_size':'\'Min size\' must be less than \'Max size\'.'}
			return False
		elif (self.created_before.data > date.today()):
			FiltersForm.errors = {'created_before':'\'Created before\' date must be before today\'s date.'}
			return False
		elif (self.updated_after.data > date.today()):
			FiltersForm.errors = {'updated_after':'\'Updated after\' date must be before today\'s date.'}
			return False
		elif (self.created_before.data > self.updated_after.data):
			FiltersForm.errors = {'created_before':'\'Created before\' date must be earlier than \'Updated after\' date.'}
			return False
		else:
			return result
