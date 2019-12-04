#!groovy

def tryStep(String message, Closure block, Closure tearDown = null) {
    try {
        block()
    }
    catch (Throwable t) {
        slackSend message: "${env.JOB_NAME}: ${message} failure ${env.BUILD_URL}", channel: '#ci-channel', color: 'danger'

        throw t
    }
    finally {
        if (tearDown) {
            tearDown()
        }
    }
}

node {
    stage("Checkout") {
        checkout scm
    }

    stage("Build Worker image") {
        tryStep "build", {
            docker.withRegistry('https://repo.data.amsterdam.nl','docker-registry') {
                def image = docker.build("datapunt/dataservices/worker:${env.BUILD_NUMBER}", "./worker")
                image.push()
            }
        }
    }

    stage('Push Worker acceptance image') {
        tryStep "image tagging", {
            docker.withRegistry('https://repo.data.amsterdam.nl','docker-registry') {
                def image = docker.image("datapunt/dataservices/worker:${env.BUILD_NUMBER}")
                image.pull()
                image.push("acceptance")
            }
        }
    }

    stage("Build Backend image") {
        tryStep "build", {
            docker.withRegistry('https://repo.data.amsterdam.nl','docker-registry') {
                def image = docker.build("datapunt/dataservices/backend:${env.BUILD_NUMBER}", "./mapserver")
                image.push()
            }
        }
    }

    stage('Push Backend acceptance image') {
        tryStep "image tagging", {
            docker.withRegistry('https://repo.data.amsterdam.nl','docker-registry') {
                def image = docker.image("datapunt/dataservices/backend:${env.BUILD_NUMBER}")
                image.pull()
                image.push("acceptance")
            }
        }
    }

    stage("Build API image") {
        tryStep "build", {
            docker.withRegistry('https://repo.data.amsterdam.nl','docker-registry') {
                def image = docker.build("datapunt/dataservices/api:${env.BUILD_NUMBER}", "./dynapi")
                image.push()
            }
        }
    }

    stage('Push API acceptance image') {
        tryStep "image tagging", {
            docker.withRegistry('https://repo.data.amsterdam.nl','docker-registry') {
                def image = docker.image("datapunt/dataservices/api:${env.BUILD_NUMBER}")
                image.pull()
                image.push("acceptance")
            }
        }
    }

    stage("Deploy to ACC") {
        tryStep "deployment", {
            build job: 'Subtask_Openstack_Playbook',
                parameters: [
                    [$class: 'StringParameterValue', name: 'INVENTORY', value: 'acceptance'],
                    [$class: 'StringParameterValue', name: 'PLAYBOOK', value: 'deploy-dataservices.yml'],
                ]
        }
    }

    stage('Waiting for approval') {
        slackSend channel: '#ci-channel', color: 'warning', message: 'Schema importer is waiting for Production Release - please confirm'
        input "Deploy to Production?"
    }

    stage('Push production images') {
        tryStep "Tag public worker image", {
            docker.withRegistry('https://repo.data.amsterdam.nl','docker-registry') {
            def image = docker.image("datapunt/dataservices/worker:${env.BUILD_NUMBER}")
                image.pull()
                image.push("production")
                image.push("latest")
            }
        }

        tryStep "Tag public backend image", {
            docker.withRegistry('https://repo.data.amsterdam.nl','docker-registry') {
            def image = docker.image("datapunt/dataservices/backend:${env.BUILD_NUMBER}")
                image.pull()
                image.push("production")
                image.push("latest")
            }
        }

        tryStep "Tag public api image", {
            docker.withRegistry('https://repo.data.amsterdam.nl','docker-registry') {
            def image = docker.image("datapunt/dataservices/api:${env.BUILD_NUMBER}")
                image.pull()
                image.push("production")
                image.push("latest")
            }
        }
    }

    stage("Deploy") {
        tryStep "deployment", {
            build job: 'Subtask_Openstack_Playbook',
            parameters: [
                [$class: 'StringParameterValue', name: 'INVENTORY', value: 'production'],
                [$class: 'StringParameterValue', name: 'PLAYBOOK', value: 'deploy-dataservices.yml'],
            ]
        }
    }

}
