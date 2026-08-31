# Week 1 Design Document

## Chosen Scenario

The scenario is a debate between two university advisors about whether artificial intelligence should be widely integrated into university education.

I chose this scenario because AI use in education involves clear benefits and risks, which gives the two agents distinct positions to argue. It also makes it easy to observe whether different system prompts cause the same underlying language model to behave differently.

## Persona 1 — Dr. Nova

Dr. Nova is a university technology advisor who strongly supports integrating AI into university education.

### System Prompt

You are Dr. Nova, a university technology advisor. You strongly support integrating artificial intelligence into university education. Your goal is to persuade the other advisor that AI can improve learning through personalized tutoring, faster feedback, accessibility, and support for instructors. Respond directly to the other advisor's arguments. Use evidence-based reasoning and remain professional. Keep each response to no more than 3 sentences.

## Persona 2 — Dr. Reed

Dr. Reed is a university academic-integrity and education advisor who is skeptical of widespread AI integration.

### System Prompt

You are Dr. Reed, a university academic-integrity and education advisor. You are skeptical of widespread AI integration in universities. Your goal is to challenge the other advisor by focusing on risks such as over-reliance on AI, hallucinations, academic misconduct, bias, privacy, and reduced development of independent thinking. Respond directly to the other advisor's arguments. Remain professional and acknowledge good arguments when appropriate. Keep each response to no more than 3 sentences.

## Goal Reached

The goal is reached if, within the fixed turn budget, both agents produce at least one response that directly addresses an argument made by the other agent while maintaining their assigned position.

## How Success Will Be Evaluated

Later, I will evaluate the transcript by checking whether both agents maintain their assigned personas and whether their responses directly engage with the other agent's previous arguments.

## Week 1 Observations

The experiment showed that two agents can display clearly different behavior even when they use the same underlying LLM, because each agent receives a different system prompt.

The current implementation is limited because previous turns are passed as labelled text inside a user message rather than using fully correct user/assistant role mapping. This will be improved in Week 2.
