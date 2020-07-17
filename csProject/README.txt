README.txt

GitHub has become the most popular web-based version control platform for open-source software, and the publicly-available GitHub API can be used to obtain information about a project and its contributors. Data can be extracted from the API which provides insight into the software development process and can be used to investigate how various factors affect code quality; for example, code change-frequency. This project employs object-orientated quality metrics to determine an overall measure of code quality for open-source Java projects. Coupled with information extracted from the GitHub API, this project further investigates the influential factors of code quality. A purpose-built tool has been developed which facilitates the investigation, allowing users to download GitHub projects, analyse their code quality and visualise the factors that influence quality. Four hypotheses were proposed regarding the effect of time, code size, change-frequency and number of contributors on code quality. Three of the four hypotheses were discovered to be valid. The results show that increasing time and code size negatively affect code quality, with increasing code size having the strongest relationship with loss of quality. Previous studies which found that the number of contributors has no significant effect on quality were corroborated. The investigation into the influence of change-frequency was inconclusive and provides an opportunity for further study.

File Structure:
	Minutes: Meeting minutes
	csProject: Application code and tests

Install Dependencies:
	pip install -r reqirements.txt

N.B. Running RQ on Windows requires a Unix emaulator, e.g. Ubuntu

Start redis server:
	(Windows CMD) redis-server --service-start
	
Start Flask app:
	(Ubuntu emulator)
	workon csproject
	Dev:
		(from mnt/c/Users/.../csProject) 
			>>> python2.7 app.py
	Production:
		(from mnt/c/Users/.../csProject) 
			>>> gunicorn -w 4 -b 127.0.0.1:5000 manage:app --timeout 6000

Start RQ worker:
	(Ubuntu emulator)
		>>> workon csproject
	(from mnt/c/Users/.../csProject)
		>>> rq worker default
