Outstanding developments:
- [ ] allow the ai to use venice ai through their openai api as model entpoint
- [ ] we need to check the DIEM balance of venice regularly because we have only a limited daily budget for inference
- [ ] we need to add groq ondemand as possible endpoint (although it has a very limited free compute budget) maybe we can use multiple accounts ?
- [ ] we need a strategy how the AI can improve itself without breaking its functionality (it should be able to test changed in a sandbox ? how to implement this ?)

Now i want to give the solution a try.
I want to run it in a proxmox container on my proxmox ve based on nixos.
Target is to get the agent running and devlop itself.

There are currently some hard limitations:
- limited budget for inference resources (we have a 0,49$ daily budget we can use on venice ai)
- limited local hardware capabilities (we could run local models using ollama, but server has only CPU no GPU)

I was thinking about how we could get mode free inference from somewhere we could use for the agent
but most services that offer inference via OpenAI API costs money.
I found groq ondemand that offers some very limited basic usage allowances that i was thinking about how we could use those.
The groq rate limits are listed here: https://console.groq.com/docs/rate-limits

Would it be possible to create several accounts on groq and setup an API key for each,
so my agent can leverage that for its development ?
I am not sure if this is feasible and how we could leverage this free usage offering.
What would you suggest ?

