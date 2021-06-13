pipeline {
    agent { label 'windows && unreal' }

    stages {
        stage ('Connect Network Drives') {
            steps {
                bat 'C:\ConnectNetworkDrives.bat'
            }
        }
        stage('InstallPrereqs') {
            steps {
                bat 'python -m pip install -r requirements.txt'
            }
        }
        stage('mypy verification') {
            steps {
                bat 'python -m mypy BlenderImporters FileUtilities RainbowFileReaders UnrealImporters tests gameLoadTest.py MAPConverter.py RSBPNGCacheGenerator.py RSBtoPNGConverter.py SOBtoOBJConverter.py'
            }
        }
        stage('Unit Test') {
            steps {
                bat 'python -m unittest discover'
            }
        }
    }
}
