"use client";
import Image from "next/image";
import React from "react";
import Input from "@/components/input/page";
import "./page.css";
import { useRouter } from "next/navigation";
const page = () => {
  const router = useRouter();
  return (
    <div className="login-page">
      <div className="login-left">
        <Image src="/assets/logo.png" height={200} width={200} alt="Logo" />
        <h2>Custom Gateways</h2>
        <p>Welcome to the platform that helps with building relationships</p>
      </div>
      <div className="login-right">
        <h1>Welcome Back!</h1>
        <Input label="Email" type="email" placeholder="youremail@gmail.com" name="email" />
        <Input label="Password" type="password" placeholder="Enter your password" name="password" />
        <button className="loginBtn" onClick={() => { localStorage.setItem("Authenticated", "True"); router.push("/dashboard"); }}>Login</button>
      </div>
    </div>
  );
};
export default page;
