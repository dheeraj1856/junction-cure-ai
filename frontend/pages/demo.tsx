import { AnimatePresence, motion } from "framer-motion";
import { RadioGroup } from "@headlessui/react";
import Link from "next/link";
import { useRef, useState, useEffect, useCallback } from "react";

const questions = [
  {
    id: 1,
    name: "Behavioral",
    description: "From LinkedIn, Amazon, Adobe",
    difficulty: "Easy",
  },
  {
    id: 2,
    name: "Technical",
    description: "From Google, Meta, and Apple",
    difficulty: "Medium",
  },
];

function classNames(...classes: string[]) {
  return classes.filter(Boolean).join(" ");
}

export default function DemoPage() {
  return (
    <AnimatePresence>
        <div className="w-full min-h-screen flex flex-col px-4 pt-2 pb-8 md:px-8 md:py-2 bg-[#FCFCFC] relative overflow-x-hidden">
          <div className="w-full flex flex-col max-w-[1080px] mx-auto mt-[10vh] overflow-y-auto pb-8 md:pb-12">
              <div className="flex flex-row items-center space-x-1">
                <p className="text-[14px] font-normal leading-[20px] text-[#1a2b3b]">
                  Demo Pages
                </p>
              </div>
          </div>
        </div>
    </AnimatePresence>
  );
}
