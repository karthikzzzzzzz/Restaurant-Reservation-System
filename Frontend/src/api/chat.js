const getResponse = async (userMessage)=>{
    try {
        console.log(userMessage);
        const response = await fetch('http://localhost:8000/v1/chat-completions', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ text: String(userMessage) }),
        });
  
        if (!response.ok) {
          throw new Error('Failed to fetch bot response');
        }
        const data = await response.json();
        const botMessage = data.responses;
        console.log(botMessage);
        return botMessage;
        
      } catch (error) {
        console.error('Error:', error);
      }
    }

export default getResponse;    
