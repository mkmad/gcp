# Overview

A cloud function is a piece of code that runs in response to an event, such as an HTTP request, a message from a messaging service, or a file upload. Cloud events are things that happen in your cloud environment. These might be things like changes to data in a database, files added to a storage system, or a new virtual machine instance being created.

Since cloud functions are event-driven, they only run when something happens. This makes them a good choice for tasks that need to be done quickly or that don't need to be running all the time.

For example, you can use a cloud function to:

- automatically generate thumbnails for images that are uploaded to Cloud Storage.
- send a notification to a user's phone when a new message is received in Cloud Pub/Sub.
- process data from a Cloud Firestore database and generate a report.
- You can write your code in any language that supports Node.js, and you can deploy your code to the cloud with a few clicks. Once your cloud function is deployed, it will automatically start running in response to events.

This hands-on lab shows you how to create, deploy, and test a cloud function using the Google Cloud console.

## Difference between Cloud Functions and Cloud Run

Google Cloud Functions and Google Cloud Run are both serverless compute platforms offered by Google Cloud Platform (GCP), but they cater to different use cases and have distinct characteristics:

*Cloud Functions:*

- Event-Driven: Cloud Functions are primarily designed to be triggered by events, such as changes in Cloud Storage, Pub/Sub messages, or HTTP requests.
- Focus on Code: You focus solely on writing the code for your function, and GCP handles the underlying infrastructure and scaling.
- Limited Customization: Cloud Functions offer less flexibility in terms of runtime environments and configuration compared to Cloud Run.
- Simplified Development: Easier to get started with and ideal for simple, event-driven tasks.

*Cloud Run:*

- Container-Based: Cloud Run runs stateless containers, giving you greater control over the runtime environment and dependencies.
- HTTP-Focused: Cloud Run is primarily designed to serve web applications and APIs over HTTP.
- Highly Customizable: You have the flexibility to use any programming language, library, or framework supported by Docker.
- Advanced Use Cases: Suitable for complex applications that require more customization and control.

## Objectives

- Create a cloud function
- Deploy and test the function
- View logs

## Create a function

In this step, you're going to create a cloud function using the console.

- In the console, click the Navigation menu (Navigation Menu icon) > Cloud Functions.
- Click Create function.
- In the Create function dialog, enter the following values:
```
Environment:            2nd Gen

Function name:          GCFunction

Region:                 REGION

Trigger type:           HTTPS

Authentication:         Allow unauthenticated invocations

Memory allocated
 (In Runtime, Build, 
 Connections and 
 Security Settings)     Keep it default

Autoscaling             Set the Maximum number of instance to 5 
```
- click Next

## Deploy the function

- Still in the Create function dialog, in Source code for Inline editor use the default helloWorld function implementation already provided for `index.js`.
    ```
    /**
    * Background Cloud Function to be triggered by Pub/Sub.
    * This function is exported by index.js, and executed when
    * the trigger topic receives a message.
    *
    * @param {object} data The event payload.
    * @param {object} context The event metadata.
    */
    exports.helloWorld = (data, context) => {
    const pubSubMessage = data;
    const name = pubSubMessage.data
        ? Buffer.from(pubSubMessage.data, 'base64').toString() : "Hello World";

    console.log(`My Cloud Function: ${name}`);
    };    
    ```
- At the bottom, click Deploy to deploy the function.
- After you click Deploy, the console redirects to the Cloud Functions Overview page.

## Test the function

- In the Cloud Functions Overview page, click on GCFunction.
- On function details dashboard, to test the function click on TESTING.
- In the Triggering event field, enter the following text between the brackets {} and click Test the function.
```
"message":"Hello World!"
```
- In the Output field, you should see the message Success: Hello World!
- In the Logs field, a status code of 200 indicates success. (It may take a minute for the logs to appear.)

## Deploy your function and attach it to Pub/Sub Topic events

When deploying a new function, you must specify `--trigger-topic`, `--trigger-bucket`, or `--trigger-http`. When deploying an update to an existing function, the function keeps the existing trigger unless otherwise specified.

For this lab, you'll set the `--trigger-topic` as `hello_world`.

```
gcloud functions deploy helloWorld \
  --stage-bucket [BUCKET_NAME] \
  --trigger-topic hello_world \
  --runtime nodejs20
```

Every message published in the topic triggers function execution, the message contents are passed as input data.

## View logs

- Click the blue arrow to go back to the Cloud Functions Overview page.
- Display the menu for your function (both the functions), and click View logs.
