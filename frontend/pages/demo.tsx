import { AnimatePresence, motion } from "framer-motion";
import { RadioGroup } from "@headlessui/react";
import Link from "next/link";
import { useRef, useState, useEffect, useCallback } from "react";
import { Disclosure } from '@headlessui/react'
import { ChevronUpIcon } from '@heroicons/react/20/solid'
import { MyDisclosure } from '../components/inputModal.jsx'
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
             <MyDisclosure />
          </div>
        </div>MyDisclosure
    </AnimatePresence>
  );
}
