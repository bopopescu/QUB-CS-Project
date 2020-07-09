from ..extensions import db
from ..models import Code_Climate, Archive, CK, Github_Stats
from app.main import code_climate
from scipy.stats.stats import pearsonr, spearmanr
from numpy import median,mean

def get_quality_scores(repositories):
	''' Returns a dict in the format { repo_name : [quality_score_v1, quality_score_v2, ...] } for each selected repository '''
	quality_scores = {}
	for repo in repositories:
		repo_versions = db.session.query(Archive).filter(Archive.github_slug==repo).order_by(Archive.timestamp).all()

		for version in repo_versions:
			ck_record = db.session.query(CK).filter(CK.archive_id==version.id).first()
			if ck_record:
				quality_scores.setdefault(version.name, list()).append(ck_record.quality_score)

	return quality_scores

def caluculate_quality_over_time(quality_scores):
	''' Returns a dict in the format { repo_name : [0, change_1, change_2, ...] } for each selected repository, where
	change_x is the difference in code quality of the current version compared to the previous version 
	(0 if current version is the first version) '''
	quality_change_over_time = {}

	for repo,scores in quality_scores.items():
		quality_change_over_time[repo] = [0]
		current_change = 0

		for idx in range( len(scores) -1 ):
			start_quality_score = scores[idx]
			end_quality_score = scores[idx+1]
			current_change += end_quality_score - start_quality_score
			quality_change_over_time[repo].append(current_change)

	return quality_change_over_time

def calculate_quality_vs_code_size(repositories):
	quality_vs_code_size = []

	for repo in repositories:
		repo_versions = db.session.query(Archive, Code_Climate, CK)\
		.filter(Archive.github_slug==repo)\
		.filter(Archive.id==Code_Climate.archive_id)\
		.filter(Archive.id==CK.archive_id)\
		.order_by(Code_Climate.lines_of_code)\
		.all()

		for version in repo_versions:
			quality_score = version.CK.quality_score
			loc = version.Code_Climate.lines_of_code
			if not loc:
				loc = code_climate.get_loc(version.Code_Climate.id)
			quality_vs_code_size.append([loc, quality_score])

	return quality_vs_code_size

def get_code_size_per_version(repositories):
	code_size_per_repo_version = {}

	for repo in repositories:
		repo_versions = db.session.query(Archive).filter(Archive.github_slug==repo).order_by(Archive.timestamp).all()

		for version in repo_versions:
			cc_record = db.session.query(Code_Climate).filter(Code_Climate.archive_id==version.id).first()
			if cc_record:
				code_size_per_repo_version.setdefault(version.name, list()).append(cc_record.lines_of_code)
	
	return code_size_per_repo_version

def calculate_change_in_code_size_between_versions(code_size_per_repo_version):
	loc_change_between_versions_per_repo = {}

	for name,versions in code_size_per_repo_version.items():
		loc_change_between_versions_per_repo[name] = [0]
		total_change = 0

		for idx in range( len(versions) -1 ):
			old_loc = versions[idx]
			current_loc = versions[idx+1]
			total_change += current_loc - old_loc
			loc_change_between_versions_per_repo[name].append(total_change)

	return loc_change_between_versions_per_repo

def caluculate_quality_vs_contributors(repositories):
	total_contributors_per_repo = []
	avg_quality_score_per_repo = []

	for repo in repositories:
		repo_versions = db.session.query(Archive, CK)\
		.filter(Archive.github_slug==repo)\
		.filter(Archive.id==CK.archive_id)\
		.order_by(Archive.timestamp)\
		.all()
		
		quality_scores = []
		for version in repo_versions:
			quality_scores.append(version.CK.quality_score)

		avg_quality_score = median(quality_scores)
		total_contributors = 0
		contribuor_records = db.session.query(Github_Stats).filter(Github_Stats.slug==repo).all()
		for record in contribuor_records:
			total_contributors += record.contributors
		
		total_contributors_per_repo.append(total_contributors)
		avg_quality_score_per_repo.append(avg_quality_score)

	return total_contributors_per_repo, avg_quality_score_per_repo

def calculate_median_quality_per_repo(quality_scores):
	median_quality_per_repo = []
	
	for name,scores in quality_scores.items():
		median_quality_per_repo.append([name, median(scores)])

	return median_quality_per_repo

def calculate_quality_change_per_repo(quality_scores):
	quality_change_per_repo = []
	for name,scores in quality_scores.items():
		quality_change_per_repo.append([name.lower(), scores[4] - scores[0]])

	return quality_change_per_repo

def calculate_avg_monthly_commits_per_repo(repositories):
	avg_monthly_commits_per_repo = []
	for repo in repositories:
		repo_stats = db.session.query(Github_Stats).filter(Github_Stats.slug==repo).first()
		if repo_stats:
			slug = repo.split('/')[1].lower()
			avg_monthly_commits_per_repo.append([slug, repo_stats.avg_monthly_commits])

	return avg_monthly_commits_per_repo

def correlate(list1, list2):
	correlation, pvalue = spearmanr(list1, list2)

	return correlation, pvalue