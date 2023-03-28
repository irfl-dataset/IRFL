# IRFL: Image Recognition of Figurative Language 

Repository for the paper "IRFL: Image Recognition of Figurative Language: https://arxiv.org/abs/2303.15445. 
Project website: https://irfl-dataset.github.io/.   
Huggingface integration + dataset card coming soon.   
Pipeline folder contains all the code for the idioms pipeline. <br>
Assets folder contain both the tasks (Understanding and Preference) and the datasets (idioms, metaphors and similes).

<a href="https://imgbb.com/"><img src="https://i.ibb.co/1qS8gRT/understanding-task.jpg" alt="understanding-task" border="0" width="400"></a>

## Abstract
Figures of speech such as metaphors, similes, and idioms allow language to be expressive, invoke emotion, and communicate abstract ideas that might otherwise be difficult to visualize. These figurative forms are often conveyed through multiple modes, such as text and images, and frequently appear in advertising, news, social media, etc. Understanding multimodal figurative language is an essential component of human communication, and it plays a significant role in our daily interactions. While humans can intuitively understand multimodal figurative language, this poses a challenging task for machines that requires the cognitive ability to map between domains, abstraction, commonsense, and profound language and cultural knowledge. In this work, we propose the Image Recognition of Figurative Language dataset to examine vision and language models' understanding of figurative language. We leverage human annotation and an automatic pipeline we created to generate a multimodal dataset and introduce two novel tasks as a benchmark for multimodal figurative understanding. We experiment with several baseline models and find that all perform substantially worse than humans. We hope our dataset and benchmark will drive the development of models that will better understand figurative language.
Our experiments demonstrate that state-of-the-art models do well when distractors are chosen randomly (~86%), but struggle with carefully chosen distractors (~53% compared to 90% human accuracy). We hope our dataset will encourage the development of new analogy-making models.
