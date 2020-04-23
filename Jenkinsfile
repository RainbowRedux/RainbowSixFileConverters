pipeline {
    agent { label 'windows' }

    stages {
        stage('InstallPrereqs') {
            steps {
                bat 'python -m pip install -r requirements.txt'
            }
        }
        stage('mypy verification') {
            steps {
                bat 'python -m mypy %WORKSPACE%'
            }
        }
        stage('Unit Test') {
            steps {
                bat 'python -m unittest discover'
            }
        }
    }
}
