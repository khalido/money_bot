# money_bot
a bot which ingests cc &amp; bank transactions, crunches them and answers questions using nlp

a basic facebook bot which:

- talks on messenger to a user
- messages get passed to python code running somewhere on the internet
- that code does some stuff and sends back a reply

voila! that all sounds so simple.

But on starting to build a parsing engine for the stuff the user is sending us, I fell for Facebook's promises of super AI powered engines and used their wit.ai NLP parser, cause they have geniuses working on it and its pre-built into messenger, so FB nlp's the user input anyways before sending it to us.

But turns out its not that great, so u need a lot of work and a bunch of if/else statements to make sense of it to be able to call relevant functions which answer the users query. Then you have to ideally hold the 'state' of the conversation somehow for each user, so the next question they ask is often related to the last few. 

This is where [Rasa Core](https://medium.com/rasa-blog/a-new-approach-to-conversational-software-2e64a5d05f2a) comes in.

> With Rasa Core, you manually specify all of the things your bot can say and do. We call these actions. One action might be to greet the user, another might be to call an API, or query a database. Then you train a probabilistic model to predict which action to take given the history of a conversation.

hmmm.. it looks great but shelved rasa core for now, going with if/else statements 
