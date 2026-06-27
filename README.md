This is a work experience finder project for the Youth Code x AI hackathon.
The idea is a web crawler or scraper made in python searchs and collects data on various websites. 
This data is processed and analyse by an AI/ML algorithm to see if it is a current work experience oppunity or other oppitunity for students. 
It will then categorise the info and display it in a visual ui. 
Please note that the crawler algorithm unfornutely is unfinshed so the wrong data is shown. I still however wishes to submit my work so far. 

To run the software:
1) Dowload it to vs code
   open terminal
   then copy this:

   git clone https://github.com/axobotlEC/workexperiencefinder
   cd workexperiencefinder
   code .

3) Open the terminal and type this if on windows:

$python='python'
python --version 2>$null
if ($LASTEXITCODE -ne 0) { py --version 2>$null; if ($LASTEXITCODE -ne 0) { Write-Error "Python not found"; exit 1 } else { $python='py' } }
& $python -m venv .venv
. .\.venv\Scripts\Activate.ps1
& $python -m pip install --upgrade pip
if (Test-Path requirements.txt) { & $python -m pip install -r requirements.txt }
$src = Get-Content app.py -Raw
if ($src -match 'streamlit') { & $python -m streamlit run app.py }
elseif ($src -match 'flask') { $env:FLASK_APP='app.py'; & $python -m flask run }
elseif ($src -match 'fastapi|uvicorn') { & $python -m uvicorn app:app --reload }
else { & $python app.py }

Or this if on mac:

python --version >/dev/null 2>&1
if [ $? -ne 0 ]; then
  if command -v py >/dev/null 2>&1; then PY=py; else echo "Python not found"; exit 1; fi
else
  PY=python
fi
$PY -m venv .venv
. .venv/bin/activate
$PY -m pip install --upgrade pip
if [ -f requirements.txt ]; then $PY -m pip install -r requirements.txt; fi
SRC=$(cat app.py)
if echo "$SRC" | grep -q streamlit; then $PY -m streamlit run app.py
elif echo "$SRC" | grep -q flask; then FLASK_APP=app.py $PY -m flask run
elif echo "$SRC" | grep -Eq 'fastapi|uvicorn'; then $PY -m uvicorn app:app --reload
else $PY app.py
fi
