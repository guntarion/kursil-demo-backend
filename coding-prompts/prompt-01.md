Ok. Now let's do something before we save it into the database.

So we have the following text as the input:

```
### Digital Marketing Training Program

Here’s a structured training program for Digital Marketing, broken down into coherent training sessions, each focusing on essential aspects of the field. 

1. **Topic Title:** Introduction to Digital Marketing
   - **Objective:** Understand the fundamentals of digital marketing and its relevance in today's business environment.
   - **Key Concepts:** Definition of digital marketing, channels of digital marketing, the importance of online presence.
   - **Skills to be Mastered:** Identifying different digital marketing channels and their respective roles.
   - **Point of Discussion:**
     - Overview of digital marketing vs traditional marketing.
     - Importance of digital marketing in business strategy.
     - The digital marketing funnel.
     - Key performance indicators (KPIs) in digital marketing.
     - Understanding the target audience in a digital context.

2. **Topic Title:** Search Engine Optimization (SEO) Basics
   - **Objective:** Learn the principles of SEO and how to optimize content for search engines.
   - **Key Concepts:** On-page SEO, off-page SEO, keyword research, and importance of backlinks.
   - **Skills to be Mastered:** Conducting keyword research and optimizing a web page for SEO.
   - **Point of Discussion:**
     - Understanding how search engines work.
     - Importance of keywords and how to choose them.
     - On-page vs off-page SEO strategies.
     - Technical SEO basics.
     - Tools for SEO analysis (e.g., Google Analytics, SEMrush).


This grid format provides a comprehensive overview of essential digital marketing topics for participants, ensuring a structured learning path that covers both theoretical knowledge and practical skills.
```

I  want to store into database into the following:

```
# main_topic collection

```
_id:ObjectId('12345678890')
main_topic : "Digital Marketing" # We obtain this from the post request
list_of_topics: Array(x)
	1: Introduction to Digital Marketing
	2: Search Engine Optimization (SEO) Basics
	3: Content Marketing Strategies
	4: Social Media Marketing Essentials
	5: Email Marketing Fundamentals
	6: Paid Advertising (PPC) Strategies
	7: Analytics and Performance Measurement
	8: Digital Marketing Trends and Innovations
```

# list_topics collection

```
# list_topics collection
_id:ObjectId('123312312345678890')
main_topic_id: "12345678890" 
topic_name: "Introduction to Digital Marketing"
objective: "Understand the fundamentals of digital marketing and its relevance in today's business environment."
key_concepts: "Definition of digital marketing, channels of digital marketing, the importance of online presence"
skills_to_be_mastered: "Identifying different digital marketing channels and their respective roles."
point_of_discussion: Object
1: "Overview of digital marketing vs traditional marketing."
2: "Importance of digital marketing in business strategy."
3: "The digital marketing funnel."
4: "Key performance indicators (KPIs) in digital marketing."
5: "Understanding the target audience in a digital context."

_id:ObjectId('123312312345678891')
main_topic_id: "12345678890" 
topic_name : "Search Engine Optimization (SEO) Basics"
objective : "Learn the principles of SEO and how to optimize content for search engines."
key_concepts : "On-page SEO, off-page SEO, keyword research, and importance of backlinks."
skills_to_be_mastered : "Conducting keyword research and optimizing a web page for SEO."
point_of_discussion: Object
1: "Understanding how search engines work."
2: "Importance of keywords and how to choose them."
3: "On-page vs off-page SEO strategies."
4: "Technical SEO basics."
5: "Tools for SEO analysis (e.g., Google Analytics, SEMrush)."

_id:ObjectId('123312312345678892')
main_topic_id: "12345678890" 
topic_name: "Content Marketing Strategies"
objective: "Develop skills to create and implement effective content marketing strategies."
key_concepts: "Types of content, content calendar, audience engagement."
skills_to_be_mastered: "Creating a content strategy and crafting compelling content pieces."
point_of_discussion: Object
1: "Understanding different types of content (blogs, videos, infographics)."
2: "Importance of storytelling in content marketing."
3: "Strategies for content distribution."
4: "Measuring content effectiveness and engagement."
5: "Tools for content creation and scheduling."

```

```






