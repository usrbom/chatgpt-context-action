**PRESS RELEASE — OPENAI**

**ChatGPT Launches the Contextual Action Engine: Your AI That Goes Beyond Understanding. It Acts for You.**

*The new feature learns how you like things done and completes real-world tasks from intent to confirmation, all without switching apps*

**Los Angeles, May 2026** — Marcus Chen was running late, again. He had forgotten to book a birthday dinner for his partner. Buried in back-to-back meetings, he pulled out his phone and typed one message into ChatGPT: *"Book us dinner Saturday at an Italian place."* ChatGPT surfaced three Italian spots that matched his taste. He picked one and tapped confirm. Thirty seconds later, a reservation confirmation was in his hand.

"I didn't even think it would actually do it," Marcus said. I didn't have to browse Yelp, cross-check availability, or even think about what she'd like. It already knew. It found the place and booked it for me.”

## **The Problem: Gap between “intent” and “action”** 

Most people don't struggle with finding information anymore. They struggle with everything that comes after. You search for a restaurant, then open another app to check availability, then remember you don't have the credit card saved, then realize you've been going back and forth for twenty minutes on something that should have taken thirty seconds. The assistant answered your question. But it didn't actually help you.

## **How It Works: From “Tell Me” to “Do It for Me”**

Marcus's experience is now available for everyone. Think of it as a personal assistant who just gets you. The more you use ChatGPT, the more it understands what you like: where you love to eat, how you like to plan, what matters to you. 

The experience works just like a regular ChatGPT conversation. No new app to download, no account to set up, or no preferences to fill in. When a user asks “can you find me a restaurant?” ChatGPT immediately gets to work. It scans user interaction history and past behavior to understand preferences such as typical price ranges, preferred locations, and past visits. It surfaces a small curated set of recommendations tailored to the user’s taste. Then the user reviews and either confirms or asks for alternatives, at which point ChatGPT refines its suggestions based on the feedback. Once a choice is made, ChatGPT collects any remaining details needed, including number of guests, name, time. Then it connects directly to the relevant third-party service to complete the booking. A full confirmation summary lands inside the ChatGPT thread within 30 seconds.

"AI has always been about saving people time. But we kept seeing the same pattern where people would research something on ChatGPT and then leave to finish the work somewhere else. That was the key friction. If you still have to do all the follow-up yourself, we haven't actually delivered our promise. The Contextual Action Engine is finally closing that gap. ChatGPT now takes you all the way from the first word of your request to the moment it's done," said Sarah Park, VP of Product at OpenAI.

## **Under the Hood: Contextual Action Engine**

How does the Contextual Action Engine work? It stores every completed action inside ChatGPT as a structured record and converts each record into a semantic embedding, a numerical representation that captures the meaning and context of that action. When a new request comes in, the engine retrieves the most contextually similar past actions by measuring vector distance rather than matching keywords, then identifies statistically significant behavioral patterns to inform its recommendations.

Before any recommendation reaches the user, it passes through three checks. First, the engine validates that the retrieved data is clean and complete. It catches missing fields, out-of-range dates, or inconsistent records. Second, it verifies that the recommendation is aligned with the user’s preference and matches the user's original request. Third, it confirms that the suggested venue exists and is bookable through a connected third-party service. If any check fails, the engine returns nothing rather than surfacing a guess.

## **Protecting Privacy and Security**

Privacy is built into the engine at every layer. At the input layer, invalid parameters and abnormal request patterns are caught and returned to the user before anything reaches an external service. At the transaction layer, any anomalous action requires a second authorization via SMS before it is executed. And across all layers, PII masking ensures that sensitive data such as names, contact details, payment information is never exposed in storage or in transit to third-party services.

Beyond data protection, user control is fundamental to how the engine operates. Nothing is booked, scheduled, or purchased without an explicit confirmation from the user. The engine never acts on assumptions. You stay in control at every step.

## **Built for Trust, Designed to Grow**

Today, the new feature is focused on restaurant reservations. OpenAI deliberately started with reservations because they represent a low-stakes, high-frequency task. This is the kind of task where OpenAI can build users’ trust in the engine's judgment before handing it more complex responsibilities. The current version handles forward bookings only. Cancellations, modifications, and more complex multi-step transactions will come as that trust is established. The goal was never to do everything at once. It was to earn the right to do more, one confirmed booking at a time.

But this is just the beginning. In the months ahead, ChatGPT will expand to hotels, flights, events, and virtually any reservation. Once a booking is confirmed, ChatGPT will automatically send a confirmation to your email and add it to your calendar so nothing slips through the cracks. It will also suggest natural add-ons to round out your plans: a park nearby for an after-dinner walk, a hotel close to your concert venue, or a coffee shop to kick off your morning before a flight. The goal is simple: if there's a reservation you need to make, ChatGPT should be able to handle it.

## Get Started!

In its initial rollout to a select group of early users, the Contextual Action Engine has already received positive response. 80% of users reported satisfaction with their first booking experience, and 10% of users returned to use the feature repeatedly within the first week, signaling a strong satisfaction. "It feels less like using an app and more like texting a friend who happens to know exactly where you like to eat," said Jamie Torres, a teacher from Chicago and early beta user. "My partner asked how I managed to book the perfect place on such short notice. I just smiled."

The Contextual Action Engine is available now for ChatGPT Plus subscribers. Whether you're planning a last-minute dinner or locking in your weekend, ChatGPT is ready to handle it\!

**Frequently Asked Questions**

**Q1: How is the Contextual Action Engine different from ChatGPT's existing memory feature?**

**A:** ChatGPT's existing memory feature stores information that users explicitly share, such as dietary restrictions, personal details, and stated preferences. The Contextual Action Engine works completely differently. Rather than relying on what you tell, it learns from what you actually do inside ChatGPT over time. If you consistently book restaurants on Friday evenings, favor a particular neighborhood, or follow a research request with a scheduling action, the engine recognizes those patterns and uses them to anticipate what you need next. And unlike memory, it doesn’t just inform a response. It completes the task on your behalf.

**Q2: What kinds of tasks can the Contextual Action Engine complete today?**

**A:** At launch, the Contextual Action Engine supports standard restaurant reservations for US-based users. This includes seated dining reservations with party size, time, date, name, and any special notes. The engine completes bookings through OpenTable's API, which means restaurants must be listed and bookable on OpenTable to be eligible. The current version handles forward bookings only. Cancellations, modifications, and walk-in requests are not supported at this stage. Support for additional platforms including Resy and Google Reservations, as well as expanded task categories like hotel and event bookings, is planned for future releases.

**Q3: What if I don't like the restaurant ChatGPT picks?**

**A:** You can always ask for alternatives. The engine refines its suggestions based on your feedback and will never execute a booking without your explicit confirmation. If the suggestion does not feel right, simply tell it what you would prefer: a different cuisine, a lower price point, a larger table, or a specific neighborhood. Nothing happens without your confirmation.

**Q4: What if I want to modify or cancel my reservation?**

**A:** At this stage, modifications and cancellations are not yet supported within ChatGPT. Please visit OpenTable directly. Your booking will be listed under your account and can be managed there. This capability is on our roadmap and will be available in a future release.

**Q5: What if the booking goes wrong or the service is unavailable?**

**A:** If a third-party service fails mid-booking or the restaurant is no longer available, ChatGPT will let you know immediately in plain language. It will explain what went wrong and suggest a clear next step, such as trying an alternative restaurant or adjusting the time. No action is ever silently dropped or completed incorrectly without your knowledge.

**Q6: How does ChatGPT handle my behavioral data?**

**A:** Behavioral data is used exclusively to improve task completion within ChatGPT and is never sold or shared with third parties for advertising purposes. Users can view, manage, and delete their action history at any time through the privacy dashboard in their account settings. Users may also opt out of behavioral inference entirely while retaining access to all of ChatGPT's other capabilities. OpenAI's data practices for the Contextual Action Engine are fully consistent with its existing privacy policy and applicable data protection regulations.

**Q7: How is my personal information protected?**

**A:** The Contextual Action Engine is built with data protection at every layer. Your behavioral data is stored under a randomized user identifier. PII masking ensures that sensitive information such as your name, phone number, and payment details are stripped from all action records before storage. Transaction data passed to third-party services is encrypted in transit, ensuring that booking details are protected from interception during transmission.

**Q8: Does this compete with or replace existing apps like OpenTable or Resy?**

**A:** No. Every reservation completed through ChatGPT is executed directly through a third-party booking platform like OpenTable. When you confirm a booking, ChatGPT connects to OpenTable's infrastructure in real time, searches availability, and completes the transaction on your behalf. ChatGPT simply removes the step of navigating there yourself.

**Q9: Why would third-party collaborate with ChatGPT?**

**A:** The integration unlocks a powerful new customer acquisition channel. By accessing ChatGPT’s huge customer base of 900M weekly users, platforms like OpenTable gains direct access to high-intent users at the moment of booking. While the integration requires a one-time API build on their end, that is a reasonable investment given the scale of demand it unlocks.

**Q10: How would this feature help defend against competitors like Google and Anthropic?**

**A:** The biggest moat is behavioral action history. Unlike stated preferences which can be exported across platforms, behavioral data cannot be transferred. Anthropic launched a memory import tool that allows users to transfer their ChatGPT conversation history directly into Claude but behavioral data stays inside ChatGPT. Every completed action deepens the dataset and enables increasingly personalized recommendations over time. While building an execution layer is technically replicable, being first increases the switching cost. Users who complete their first booking through ChatGPT will return for the next one, rather than switching to a different platform and starting from scratch.

**Q11: Why is now the right moment to launch?**

**A:** Three market conditions converged to make this the right moment. First, GPT-5 reduced hallucinations by 80% compared to prior models, making ChatGPT reliable enough to complete consequential real-world actions like bookings and purchases on a user's behalf. Second, consumer behavior is evolving. Users are no longer satisfied with just finding information, but they expect AI to help them act on it too. Third, no competitor has yet established a dominant execution layer for consumer daily life. ChatGPT is uniquely positioned to make that leap first and claim the category before anyone else does.

**Q12: Why not launch the full ChatGPT Life OS?**

**A:** The fundamental question behind the Contextual Action Engine is whether users will trust AI to complete real-world tasks on their behalf. Restaurant reservations are low-stakes where mistakes are easily corrected and frequent enough to generate meaningful data quickly. A high-stakes failure could permanently damage user confidence before trust is ever established. Starting small also generates real behavioral insight into what users actually want, revealing how they respond to recommendations, where they hesitate, and what they confirm or reject. Those insights will directly shape the roadmap, ensuring the full ChatGPT Life OS is built on what users actually need rather than what we assume they want.

**Q13: What does success look like?**

**A:** At the technical level, the engine must achieve 90% fully correct completions on the golden dataset, with booking parameter accuracy at 99% since incorrect parameters result in real-world consequences for the user. Hallucination rate must stay below 5% and the engine should never surface a restaurant that doesn't exist or confirm a time slot that isn't available. Response latency must hit a P50 of under 3 seconds to avoid users abandoning the flow mid-booking.

At the business level, success is defined by genuine adoption rather than curiosity-driven usage. Task completion rate, the percentage of users who initiate a booking and reach a confirmed reservation, is the primary signal. Repeat usage rate where users complete 2 or more bookings signals that the engine has earned a place in their routine. A meaningful decrease in users leaving ChatGPT to complete booking elsewhere would confirm that the engine is successful in closing the loop from intent to execution.

**Q14: How does it make money?**

**A:** The Contextual Action Engine monetizes through two mechanisms. First, it helps reduce churn among existing Plus subscribers. Current one-year retention for Plus sits at 59%, leaving meaningful room to improve. The new feature that saves users time on daily tasks gives them a concrete, recurring reason to stay subscribed. Second, it helps drive upgrades from free users to Plus. With 900 million weekly users and a current free-to-paid conversion rate of 2-3%, even a modest improvement in conversion represents millions of new paying subscribers.

**Q15: How do you ensure the engine stays consistent as the underlying AI is updated?**

**A:** Every model update is validated against a golden dataset of 150 prompts before deployment, covering realistic booking scenarios, edge cases, and adversarial inputs. The engine must achieve 90% fully correct completions to pass. To prevent eval set staleness, the golden dataset is continuously updated alongside the model to ensure test cases remain relevant to new failure modes. Evaluation uses a hybrid approach where an agent judge handles ongoing testing at scale, while human reviewers periodically grade a sample of outputs and compare against the judge. If discrepancies exceed 25%, the judge model is recalibrated before the next release.

**Q16: How does the engine handle malicious or manipulative inputs?**

**A:** Adversarial inputs are handled at multiple layers before they can affect a real-world transaction. At the input layer, invalid parameters and abnormal request patterns are caught and returned to the user before itching any external services, such as repeated identical bookings or impossible dates. For any action flagged as anomalous, a second authorization via SMS is required before the transaction is completed. This means that even if someone gains unauthorized access to your account, they cannot complete a booking without your knowledge.

**Q17: How do you ensure reliability when dependent on third-party APIs?**

**A:** Third-party API dependency is one of the most significant technical risks for the Contextual Action Engine. When an external API call fails, the engine surfaces the failure to the user immediately with a clear recovery path rather than dropping the task silently. Task completion rate is tracked as a primary guardrail metric so that any statistically significant increase in failure rate triggers an automatic review before the issue compounds at scale. API failure scenarios are also explicitly represented in the golden dataset, ensuring failure handling is tested and verified before every model update.