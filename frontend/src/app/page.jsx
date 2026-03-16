"use client";
import { useRouter } from "next/navigation";
import React, { useEffect } from "react";
const page = () => {
  const router = useRouter();
  useEffect(() => {
    if (typeof window !== "undefined") {
      const loggedIn = localStorage.getItem("Authenticated") === "True";
      router.replace(loggedIn ? "/dashboard" : "/login");
    }
  }, [router]);
  return <div>Loading...</div>;
};
export default page;
