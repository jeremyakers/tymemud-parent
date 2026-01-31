Here is the updated **Channeling System Design Document**. I have incorporated the technical resolutions for Flow Buffering, Fizzle/Backfire mechanics, and the combat Charge/Tick system.

# **WoT MUD: Channeling System Design Document**

## **1\. System Overview**

The Channeling system mirrors the Wheel of Time lore, utilizing the Five Flows (**Air, Water, Spirit, Fire, Earth**). It is a "Pattern-based" system where players learn by observing others and refine their abilities through practice.

## ---

**2\. Core Stats & Potency (OFA)**

### **2.1 The Five Flows**

Each character has a rating (1–4) in each of the five elements. These ratings determine:

* **Knowledge Potential**: Which weaves can be learned.  
* **Flow Potency**: The effectiveness of a weave's elemental component.  
* **Finesse**: A specialized modifier for "delicate" weaves (e.g., Healing, Compulsion). Higher Finesse increases learning speed by 50% and reduces "Fizzle" chances.

### **2.2 Offensive Flow Ability (OFA)**

OFA is the primary scaling factor for weave damage and duration.

* **Calculation**: Use the logic in calculate\_OFA.txt.  
* **Scaling**: For characters with TALENT\_ACTIVE\_CHANNELER, OFA scales with level to ensure they aren't forced to maximize physical stats (Str/Dex) to be effective weavers.

## ---

**3\. Teaching, Learning, & Mastery**

### **3.1 Observation Logic**

Players do not use trainers. They learn through the watch and teach commands.

* **Knowledge vs. Ability**: A player can "know" a weave's pattern (stored in weave\_knowledge) but lack the flow strength to manifest it.  
* **Learning Speed**: Chance \= Base\_Chance \* Finesse\_Mod \* Intelligence\_Mod.

### **3.2 The "Fizzle" & Backfire Mechanic**

If a player attempts a weave where their Mastery or Flow Strength is lower than the weave's Min\_Requirement:

* **Failure Chance**: 1.0 \- (Current\_Strength / Required\_Strength).  
* **Backfire**: On a "Fizzle," the player loses 20% of their **Max Willpower** and is **Stunned** for 1 combat round as the flows collapse.

## ---

**4\. Combat Integration: The "Charge" System**

Channeling in combat is not instant; it requires holding and weaving flows over time.

### **4.1 Tick Costs (Combat Turns)**

Weaves have a **Tick Cost** based on their manifested Strength Level:

* **Level 1 (Minimal)**: 0 Ticks (Resolves at the end of the current round).  
* **Level 2 (Normal)**: 1 Tick (Resolves at the end of the next round).  
* **Level 3 (High)**: 2 Ticks.  
* **Level 4 (Overchannel)**: 3 Ticks.

### **4.2 Vulnerability & Interruption**

* **Readiness Penalty**: While "Charging" a weave, the channeler's Defense Readiness is halved (0.5 modifier).  
* **Breaking Flows**: If the channeler receives a **Substantial Wound** or higher (20%+ part damage) while charging, the weave is broken and a "Fizzle" check is triggered.

## ---

**5\. UI & Flow Buffering**

To prevent overwhelming syntax, the system uses **Flow Buffering**.

* **Player Command**: weave 'fireball' 3 \<target\>  
* **System Logic**: The code automatically allocates the required Air and Fire flows based on the player’s best available ratios for "Level 3 Fireball."

## ---

**6\. Technical Data Structures (For Cursor)**

### **6.1 Weave Definition**

C

struct weave\_data {  
    int id;  
    char \*name;  
    int flow\_reqs\[5\];      // \[Air, Water, Spirit, Fire, Earth\]  
    int min\_mastery;       // Minimum mastery to avoid backfire  
    int base\_will\_cost;  
    int tick\_cost\_base;  
    int damage\_type;       // Tied to Combat System (Slash/Pierce/Crush/OnePower)  
    bool is\_finesse\_based; // If true, uses Finesse instead of Strength for OFA  
};

### **6.2 Channeler Mastery**

C

struct char\_weave\_mastery {  
    int weave\_id;  
    int mastery\_level;     // 0-1000  
    bool can\_manifest;     // Calculated: True if flows \>= weave\_reqs  
};

## ---

**7\. Implementation Requirements for Cursor**

1. **OFA Integration**: Implement the calculate\_OFA function and ensure it is called during the resolve\_weave phase.  
2. **Willpower Check**: Ensure Mental Endurance (Willpower) is checked *before* and *after* the charge phase.  
3. **Wound Hook**: In the combat resolve\_turn function, add a hook: if (GET\_WOUND\_SEVERITY(victim) \>= SUBSTANTIAL) break\_flows(victim);.  
4. **Teaching Logic**: Implement the teach command to provide a \+25% bonus to the student's learning roll.