package com.sonata.app.tts.phonemizer

import java.util.regex.Pattern

object EnglishPhonemizer {
    private val vowels = "aeiou"
    private val consonants = "bcdfghjklmnpqrstvwxyz"
    
    private val phonemeMap = mapOf(
        "a" to "AH0", "e" to "EH0", "i" to "IH0", "o" to "OW0", "u" to "UH0",
        "b" to "B", "c" to "K", "d" to "D", "f" to "F", "g" to "G",
        "h" to "HH", "j" to "JH", "k" to "K", "l" to "L", "m" to "M",
        "n" to "N", "p" to "P", "q" to "K", "r" to "R", "s" to "S",
        "t" to "T", "v" to "V", "w" to "W", "x" to "K S", "y" to "Y",
        "z" to "Z", "th" to "TH", "ch" to "CH", "sh" to "SH", "ng" to "NG",
        "ee" to "IY", "oo" to "UW", "ai" to "EY", "ou" to "AW",
        "ie" to "IY", "ea" to "IY", "ou" to "AW", "au" to "AO"
    )

    fun phonemize(text: String): List<String> {
        val result = mutableListOf<String>()
        val cleaned = text.lowercase().replace(Regex("[^a-z ]"), "")
        val words = cleaned.split(Regex("\\s+"))
        
        for (word in words) {
            if (word.isNotEmpty()) {
                val phonemes = wordToPhonemes(word)
                result.addAll(phonemes)
                result.add("PAUSE")
            }
        }
        
        return result
    }

    private fun wordToPhonemes(word: String): List<String> {
        val result = mutableListOf<String>()
        var i = 0
        
        while (i < word.length) {
            var matched = false
            
            // Try three-letter combinations
            if (i + 2 < word.length) {
                val tri = word.substring(i, i + 3)
                phonemeMap[tri]?.let {
                    result.add(it)
                    i += 3
                    matched = true
                }
            }
            
            // Try two-letter combinations
            if (!matched && i + 1 < word.length) {
                val bi = word.substring(i, i + 2)
                phonemeMap[bi]?.let {
                    result.add(it)
                    i += 2
                    matched = true
                }
            }
            
            // Single letter
            if (!matched) {
                phonemeMap[word[i].toString()]?.let {
                    result.add(it)
                } ?: result.add(word[i].uppercase())
                i++
            }
        }
        
        return result
    }
}