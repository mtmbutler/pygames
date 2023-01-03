package main

import (
	"bufio"
	"fmt"
	"log"
	"math/rand"
	"os"
	"time"
)

var (
	PROMPTS_PATH                    = "./scattergories.txt"
	LETTERS                         = []rune("ABCDEFGHIJKLMNOPRSTW")
	NUM_PROMPTS                     = 12
	SECONDS_PER_ROUND time.Duration = 180 * time.Second
	RESOLUTION        time.Duration = 100 * time.Millisecond
	SEP                             = "==="
)

func getPrompts() ([]string, error) {
	file, err := os.Open(PROMPTS_PATH)
	if err != nil {
		return []string{}, err
	}
	defer file.Close()

	prompts := []string{}
	scanner := bufio.NewScanner(file)
	for scanner.Scan() {
		prompts = append(prompts, scanner.Text())
	}
	if err := scanner.Err(); err != nil {
		return []string{}, err
	}
	return prompts, nil
}

func main() {
	fmt.Println("Welcome to Scattergories!")

	// Shuffle inputs
	prompts, err := getPrompts()
	if err != nil {
		log.Fatal(err)
	}
	rand.Seed(time.Now().UnixNano())
	rand.Shuffle(len(LETTERS), func(i, j int) {
		LETTERS[i], LETTERS[j] = LETTERS[j], LETTERS[i]
	})
	rand.Shuffle(len(prompts), func(i, j int) {
		prompts[i], prompts[j] = prompts[j], prompts[i]
	})

	// Loop
	var letter rune
	var prompt string
	for {
		// Print instructions and wait for enter
		fmt.Print("Press enter to start a round.")
		fmt.Scanln()

		// Show letter and prompts
		fmt.Println(SEP)
		letter, LETTERS = LETTERS[0], LETTERS[1:]
		fmt.Printf("Letter: %s\n", string(letter))
		fmt.Println("Prompts:")
		for i := 0; i < NUM_PROMPTS; i++ {
			prompt, prompts = prompts[0], prompts[1:]
			fmt.Printf("  %d.\t%s\n", i, prompt)
		}
		fmt.Println("")

		// Show timer until round ends or is interrupted
		start := time.Now()
		current := start
		target := start.Add(SECONDS_PER_ROUND)
		for current.Before(target) {
			delta := int(target.Sub(current).Seconds())
			fmt.Printf("\rRemaining time: %dm%ds", delta/60, delta%60)
			time.Sleep(RESOLUTION)
			current = time.Now()
		}
		fmt.Println("Time's up!")
		fmt.Println(SEP)
	}
}
