footer: TeamKernel, 2017

# moneybot

conversational interface to your finances

## by #teamkernel

---

# problem

## easily access and analyze my transactions

## know my spending habits

my bank and apps like pocketbook tdon't do a good enough job.

---

## know thy incoming data

![left, fit](static/bank_detect_classify.png)

---

# automated parsing

![left](static/bank detect.png)

---

# transaction classification > 80%

![fill, inline](static/classifier.png)

---

# why does my bank suck at classifying my transactions?

features, features, features![^1]

- used word2vec and sklearn to classify
- turns out the big guys use yellow pages and humans
- we used a number of algos from sklearn

[^1]: ok, maybe not so many

---

# need NLP to understand text

![inline](static/ai_xkcd.png)

- we're using facebook's wit.ai engine to parse text
- fb AI promises the world, but needs a lot of work [^fb]

---

# short demo

moneybot, where art thou?

---

# handle more intents in the future

### by using a LSTM NN to connect incoming intents to actions with memory

![fit](static/if_else_intent.png)

---

![inline](static/twitter_bot_xkcd.png)

of course, a few years from now...

---

# [fit] questions?