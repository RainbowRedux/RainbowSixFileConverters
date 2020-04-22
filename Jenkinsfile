pipeline {
    agent { label 'windows' }

    stages {
        stage('InstallPrereqs') {
            steps {
                bat 'python -m pip -r requirements.txt'
            }
        }
        stage('mypy verification') {
            steps {
                bat 'python -m mypy .'
            }
        }
        stage('Unit Test') {
            steps {
                bat 'python -m unittest discover'
            }
        }
    }
}
