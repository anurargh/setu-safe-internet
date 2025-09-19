import React, { useState } from "react";

export default function LoginForm() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const handleLogin = (e) => {
    e.preventDefault(); // stop page reload

    // Build login payload
    const payload = {
      email,
      password,
    };

    // Example: send to backend API
    fetch("http://localhost:5000/login", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    })
      .then((res) => {
        if (!res.ok) throw new Error("Login failed");
        return res.json();
      })
      .then((data) => {
        console.log("Login successful:", data);
        // e.g. store token, redirect, etc.
      })
      .catch((err) => {
        console.error(err.message);
      });
  };

  return (
    <form onSubmit={handleLogin} className="flex flex-col gap-3 w-64">
      <input
        type="email"
        placeholder="Email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        className="border rounded p-2"
        required
      />
      <input
        type="password"
        placeholder="Password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        className="border rounded p-2"
        required
      />
      <button type="submit" className="bg-blue-600 text-white rounded p-2">
        Login
      </button>
    </form>
  );
}
