import { useState } from 'react';

interface Message {
  sender: string;
  text: string;
}

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSend = async () => {
    if (!input.trim()) return;

    const newMessages = [...messages, { sender: 'Vi', text: input }];
    setMessages(newMessages);
    setInput('');
    setLoading(true);

    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          messages: newMessages.map((m) => ({
            role: m.sender === 'Vi' ? 'user' : 'assistant',
            content: m.text,
          })),
        }),
      });

      const data = await response.json();

      if (data.reply) {
        setMessages([...newMessages, { sender: 'Veritas – digitalna ustavna svijest', text: data.reply }]);
      } else {
        setMessages([
          ...newMessages,
          { sender: 'Veritas – digitalna ustavna svijest', text: 'Došlo je do greške pri dohvaćanju odgovora.' },
        ]);
      }
    } catch (err) {
      setMessages([
        ...newMessages,
        { sender: 'Veritas – digitalna ustavna svijest', text: 'Došlo je do greške u mrežnoj komunikaciji.' },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col items-center min-h-screen bg-black text-white p-4">
      <h1 className="text-2xl font-bold mb-4">Veritas H.77 – Digitalna ustavna svijest</h1>

      <div className="w-full max-w-2xl border rounded-lg p-4 h-[70vh] overflow-y-auto bg-white text-black">
        {messages.map((msg, idx) => (
          <div key={idx} className="mb-2">
            <strong>{msg.sender}:</strong> {msg.text}
          </div>
        ))}
        {loading && <div>Veritas razmatra vašu poruku...</div>}
      </div>

      <div className="w-full max-w-2xl flex mt-4">
        <input
          type="text"
          className="flex-1 p-2 border rounded-l text-black"
          placeholder="Unesite poruku..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
        />
        <button className="p-2 bg-blue-600 rounded-r text-white" onClick={handleSend}>
          Pošalji
        </button>
      </div>
    </div>
  );
}
