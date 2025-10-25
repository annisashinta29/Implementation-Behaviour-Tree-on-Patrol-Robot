## **Behaviour Tree Patrol Robot**

🌲 Behaviour Tree Structure

Struktur utama Behaviour Tree yang digunakan terdiri dari beberapa Sequence node:
| Node              | Fungsi                                          | Kondisi / Aksi                       |
| ----------------- | ----------------------------------------------- | ------------------------------------ |
| **AvoidObstacle** | Menghindari rintangan                           | `check_obstacle → avoid_obstacle`    |
| **ChaseIntruder** | Mengejar penyusup                               | `intruder_detected → chase_intruder` |
| **LowBattery**    | Pergi ke stasiun pengisian                      | `low_battery → go_charge`            |
| **Idle**          | Diam sementara setelah beberapa kali patroli    | `patrol_done → idle`                 |
| **Patrol**        | Menjalankan patroli secara berulang di waypoint | `patrol`                             |

🧩 **Fitur Utama**
- Continuous Patrol — Robot berkeliling waypoint (A–B–C) secara berulang.
- Obstacle Avoidance — Menghindari halangan dengan logika vektor.
- Intruder Detection — Klik pada arena untuk menambahkan posisi penyusup yang akan dikejar robot.
- Battery System — Baterai berkurang saat bergerak, dan robot otomatis menuju stasiun pengisian jika <20%.
- Idle State — Setelah beberapa siklus patroli dan baterai masih tinggi, robot akan beristirahat sementara.
- Interactive GUI — Menampilkan status robot secara real-time: mode, baterai, siklus patroli, dan kontrol tombol.

🖼️ **Look interface**
- Area kiri (700×700 px): arena simulasi dengan waypoint, obstacle, intruder, dan charging station.
- Area kanan (sidebar): menampilkan status behavior tree, baterai, dan tombol kontrol.

📁 S**truktur File**
```bash
.
├── Behaviour_tree_patroll_robot.py   # File utama simulasi
├── robot.png                         # (opsional) ikon robot
├── Screenshot from 2025-10-25 16-02-12.png   # Diagram BT
└── README.md                         # Dokumentasi proyek
```

⚙️ **Instalasi & Running**
A. Pastikan Python 3.8+ sudah terpasang.
```bash
pip install pygame
```

B. Jalankan Simulasi
```bash
python3 Behaviour_tree_patroll_robot.py
```

**Diagram BT Robot**
<img width="1371" height="424" alt="Screenshot from 2025-10-25 16-02-12" src="https://github.com/user-attachments/assets/3f511703-7a0c-4afa-8b8f-5e2ad608e297" />



