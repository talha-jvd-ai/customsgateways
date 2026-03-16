"use client";
import { useEffect } from "react";
const ClientLenis = () => {
  useEffect(() => {
    import("lenis").then(({ default: Lenis }) => {
      const lenis = new Lenis({ lerp: 0.05, smoothWheel: true, touchMultiplier: 2 });
      let raf = (time) => { lenis.raf(time); requestAnimationFrame(raf); };
      requestAnimationFrame(raf);
    });
  }, []);
  return null;
};
export default ClientLenis;
