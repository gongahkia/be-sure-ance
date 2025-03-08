make:config

config:requirements.txt
	pip install -r requirements.txt
	playwright install chromium