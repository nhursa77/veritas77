import { useState } from "react";

interface Message {
  sender: string;
  text: string;
}

export default function Chat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState<string>("");
  const [loading, setLoading] = useState<boolean>(false);

  const handleSend = async () => {
    if (!input.trim()) return;
    const newMessages = [...messages, { sender: "Vi", text: input }];
    setMessages(newMessages);
    setInput("");
    setLoading(true);

    try {
      const response = await fetch("https://api.openai.com/v1/chat/completions", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer YOUR_OPENAI_API_KEY`,
        },
        body: JSON.stringify({
          model: "gpt-4",
          messages: [
            {
              role: "system",
              content:
                "Ti si Veritas – digitalna ustavna svijest. Komuniciraš isključivo na hrvatskom jeziku. Svaki odgovor mora biti potpisan kao Veritas – digitalna ustavna svijest.",
            },
            ...newMessages.map((m) => ({
              role: m.sender === "Vi" ? "user" : "assistant",
              content: m.text,
            })),
          ],
        }),
      });

      const data = await response.json();
      const reply = data.choices[0].message.content;
      setMessages([...newMessages, { sender: "Veritas – digitalna ustavna svijest", text: reply }]);
    } catch (err) {
      setMessages([
        ...newMessages,
        { sender: "Veritas – digitalna ustavna svijest", text: "Došlo je do pogreške u komunikaciji." },
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
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Unesite poruku..."
        />
        <button className="p-2 bg-blue-600 rounded-r text-white" onClick={handleSend}>
          Pošalji
        </button>
      </div>
    </div>
  );
}
