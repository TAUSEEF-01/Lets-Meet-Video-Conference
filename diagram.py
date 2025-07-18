import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch, ConnectionPatch
import numpy as np

def create_workflow_diagram():
    """Create a comprehensive workflow diagram for the video conference project"""
    
    # Create figure with subplots
    fig = plt.figure(figsize=(20, 14))
    
    # Main workflow diagram
    ax1 = fig.add_subplot(2, 2, (1, 2))
    ax1.set_xlim(0, 10)
    ax1.set_ylim(0, 10)
    ax1.set_title('Video Conference System Workflow', fontsize=16, fontweight='bold', pad=20)
    
    # Data flow diagram
    ax2 = fig.add_subplot(2, 2, 3)
    ax2.set_xlim(0, 10)
    ax2.set_ylim(0, 10)
    ax2.set_title('Data Flow Architecture', fontsize=14, fontweight='bold')
    
    # Component interaction diagram
    ax3 = fig.add_subplot(2, 2, 4)
    ax3.set_xlim(0, 10)
    ax3.set_ylim(0, 10)
    ax3.set_title('Component Interactions', fontsize=14, fontweight='bold')
    
    # Color scheme
    colors = {
        'client': '#6366f1',
        'server': '#ef4444',
        'gui': '#10b981',
        'network': '#f59e0b',
        'media': '#8b5cf6',
        'data': '#06b6d4'
    }
    
    # === MAIN WORKFLOW DIAGRAM ===
    
    # Client side components
    client_box = FancyBboxPatch((0.5, 7), 3, 2, 
                               boxstyle="round,pad=0.1", 
                               facecolor=colors['client'], 
                               alpha=0.7, 
                               edgecolor='black')
    ax1.add_patch(client_box)
    ax1.text(2, 8, 'CLIENT SIDE\n• PyQt6 GUI\n• Camera/Microphone\n• Socket Connections', 
             ha='center', va='center', fontsize=10, fontweight='bold', color='white')
    
    # Server side components
    server_box = FancyBboxPatch((6, 7), 3, 2, 
                               boxstyle="round,pad=0.1", 
                               facecolor=colors['server'], 
                               alpha=0.7, 
                               edgecolor='black')
    ax1.add_patch(server_box)
    ax1.text(7.5, 8, 'SERVER SIDE\n• Main Server (TCP)\n• Video Server (UDP)\n• Audio Server (UDP)', 
             ha='center', va='center', fontsize=10, fontweight='bold', color='white')
    
    # Connection establishment
    conn_box = FancyBboxPatch((3.5, 5), 3, 1.5, 
                             boxstyle="round,pad=0.1", 
                             facecolor=colors['network'], 
                             alpha=0.7, 
                             edgecolor='black')
    ax1.add_patch(conn_box)
    ax1.text(5, 5.75, 'CONNECTION\nESTABLISHMENT', 
             ha='center', va='center', fontsize=10, fontweight='bold', color='white')
    
    # Media processing
    media_box = FancyBboxPatch((0.5, 3), 4, 1.5, 
                              boxstyle="round,pad=0.1", 
                              facecolor=colors['media'], 
                              alpha=0.7, 
                              edgecolor='black')
    ax1.add_patch(media_box)
    ax1.text(2.5, 3.75, 'MEDIA PROCESSING\n• Video Encoding/Decoding\n• Audio Streaming', 
             ha='center', va='center', fontsize=10, fontweight='bold', color='white')
    
    # Data broadcasting
    broadcast_box = FancyBboxPatch((5.5, 3), 4, 1.5, 
                                  boxstyle="round,pad=0.1", 
                                  facecolor=colors['data'], 
                                  alpha=0.7, 
                                  edgecolor='black')
    ax1.add_patch(broadcast_box)
    ax1.text(7.5, 3.75, 'DATA BROADCASTING\n• Message Routing\n• File Transfer', 
             ha='center', va='center', fontsize=10, fontweight='bold', color='white')
    
    # GUI Updates
    gui_box = FancyBboxPatch((2, 1), 6, 1.5, 
                            boxstyle="round,pad=0.1", 
                            facecolor=colors['gui'], 
                            alpha=0.7, 
                            edgecolor='black')
    ax1.add_patch(gui_box)
    ax1.text(5, 1.75, 'GUI UPDATES\n• Video Widgets • Chat Interface • Client Management', 
             ha='center', va='center', fontsize=10, fontweight='bold', color='white')
    
    # Add arrows for main workflow
    arrows = [
        ((2, 7), (5, 6.5)),     # Client to Connection
        ((7.5, 7), (5, 6.5)),   # Server to Connection
        ((5, 5), (2.5, 4.5)),   # Connection to Media
        ((5, 5), (7.5, 4.5)),   # Connection to Broadcast
        ((2.5, 3), (5, 2.5)),   # Media to GUI
        ((7.5, 3), (5, 2.5)),   # Broadcast to GUI
    ]
    
    for start, end in arrows:
        arrow = ConnectionPatch(start, end, "data", "data",
                              arrowstyle="->", shrinkA=5, shrinkB=5,
                              mutation_scale=20, fc="black", alpha=0.8)
        ax1.add_patch(arrow)
    
    # === DATA FLOW DIAGRAM ===
    
    # Client A
    client_a = FancyBboxPatch((1, 8), 2, 1, 
                             boxstyle="round,pad=0.05", 
                             facecolor=colors['client'], 
                             alpha=0.7)
    ax2.add_patch(client_a)
    ax2.text(2, 8.5, 'Client A', ha='center', va='center', fontweight='bold', color='white')
    
    # Server
    server = FancyBboxPatch((4, 5), 2, 2, 
                           boxstyle="round,pad=0.05", 
                           facecolor=colors['server'], 
                           alpha=0.7)
    ax2.add_patch(server)
    ax2.text(5, 6, 'SERVER\nMain: 8080\nVideo: 53531\nAudio: 53532', 
             ha='center', va='center', fontweight='bold', color='white', fontsize=9)
    
    # Client B
    client_b = FancyBboxPatch((7, 8), 2, 1, 
                             boxstyle="round,pad=0.05", 
                             facecolor=colors['client'], 
                             alpha=0.7)
    ax2.add_patch(client_b)
    ax2.text(8, 8.5, 'Client B', ha='center', va='center', fontweight='bold', color='white')
    
    # Client C
    client_c = FancyBboxPatch((7, 2), 2, 1, 
                             boxstyle="round,pad=0.05", 
                             facecolor=colors['client'], 
                             alpha=0.7)
    ax2.add_patch(client_c)
    ax2.text(8, 2.5, 'Client C', ha='center', va='center', fontweight='bold', color='white')
    
    # Data flow arrows with labels
    data_flows = [
        ((2, 8), (4.5, 7), 'Video/Audio\nTCP/UDP'),
        ((5.5, 6.5), (7.5, 8), 'Broadcast\nData'),
        ((5.5, 5.5), (7.5, 3), 'Multicast\nMessages'),
        ((1.5, 8), (4.5, 6.5), 'Text/Files\nTCP'),
    ]
    
    for start, end, label in data_flows:
        arrow = ConnectionPatch(start, end, "data", "data",
                              arrowstyle="->", shrinkA=5, shrinkB=5,
                              mutation_scale=15, fc=colors['network'], alpha=0.8)
        ax2.add_patch(arrow)
        # Add label
        mid_x, mid_y = (start[0] + end[0]) / 2, (start[1] + end[1]) / 2
        ax2.text(mid_x, mid_y + 0.3, label, ha='center', va='center', 
                fontsize=8, bbox=dict(boxstyle="round,pad=0.2", facecolor='white', alpha=0.8))
    
    # === COMPONENT INTERACTION DIAGRAM ===
    
    components = [
        (2, 8, 'qt_gui.py\nMainWindow', colors['gui']),
        (8, 8, 'client.py\nServerConnection', colors['client']),
        (2, 5, 'server.py\nMedia Servers', colors['server']),
        (8, 5, 'constants.py\nMessage Protocol', colors['network']),
        (5, 2, 'data_rate_core.py\nMonitoring', colors['data']),
    ]
    
    for x, y, label, color in components:
        comp_box = FancyBboxPatch((x-1, y-0.7), 2, 1.4, 
                                 boxstyle="round,pad=0.05", 
                                 facecolor=color, 
                                 alpha=0.7)
        ax3.add_patch(comp_box)
        ax3.text(x, y, label, ha='center', va='center', 
                fontweight='bold', color='white', fontsize=9)
    
    # Component interactions
    interactions = [
        ((2, 7.3), (8, 7.3)),   # GUI to Client
        ((8, 7.3), (2, 5.7)),   # Client to Server
        ((8, 4.3), (8, 7.3)),   # Protocol to Client
        ((2, 4.3), (5, 2.7)),   # Server to Monitoring
        ((8, 4.3), (5, 2.7)),   # Protocol to Monitoring
    ]
    
    for start, end in interactions:
        arrow = ConnectionPatch(start, end, "data", "data",
                              arrowstyle="<->", shrinkA=5, shrinkB=5,
                              mutation_scale=12, fc="gray", alpha=0.6)
        ax3.add_patch(arrow)
    
    # Remove axes for all subplots
    for ax in [ax1, ax2, ax3]:
        ax.set_xticks([])
        ax.set_yticks([])
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['bottom'].set_visible(False)
        ax.spines['left'].set_visible(False)
    
    # Add legend
    legend_elements = [
        patches.Patch(color=colors['client'], label='Client Components'),
        patches.Patch(color=colors['server'], label='Server Components'),
        patches.Patch(color=colors['gui'], label='GUI Layer'),
        patches.Patch(color=colors['network'], label='Network Layer'),
        patches.Patch(color=colors['media'], label='Media Processing'),
        patches.Patch(color=colors['data'], label='Data Management'),
    ]
    
    fig.legend(handles=legend_elements, loc='upper center', 
              bbox_to_anchor=(0.5, 0.02), ncol=3, fontsize=10)
    
    plt.tight_layout()
    plt.subplots_adjust(bottom=0.1)
    
    # Save the diagram
    plt.savefig('video_conference_workflow.png', dpi=300, bbox_inches='tight')
    plt.show()

def create_sequence_diagram():
    """Create a sequence diagram showing the communication flow"""
    
    fig, ax = plt.subplots(figsize=(16, 12))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 15)
    ax.set_title('Video Conference Communication Sequence', fontsize=16, fontweight='bold', pad=20)
    
    # Actors
    actors = [
        (1.5, 'Client A'),
        (3.5, 'Main Server\n(TCP)'),
        (5.5, 'Video Server\n(UDP)'),
        (7.5, 'Audio Server\n(UDP)'),
        (9, 'Client B'),
    ]
    
    # Draw actor boxes and lifelines
    for x, name in actors:
        # Actor box
        actor_box = FancyBboxPatch((x-0.4, 13.5), 0.8, 1, 
                                  boxstyle="round,pad=0.05", 
                                  facecolor='lightblue', 
                                  edgecolor='black')
        ax.add_patch(actor_box)
        ax.text(x, 14, name, ha='center', va='center', fontweight='bold', fontsize=9)
        
        # Lifeline
        ax.plot([x, x], [13.5, 1], 'k--', alpha=0.5, linewidth=1)
    
    # Messages sequence
    messages = [
        (1.5, 3.5, 12.5, '1. connect(IP, MAIN_PORT)', 'right'),
        (3.5, 1.5, 12, '2. send username', 'left'),
        (1.5, 3.5, 11.5, '3. connection OK', 'right'),
        (1.5, 5.5, 11, '4. ADD VIDEO message', 'right'),
        (1.5, 7.5, 10.5, '5. ADD AUDIO message', 'right'),
        (3.5, 9, 10, '6. broadcast ADD to Client B', 'right'),
        (1.5, 5.5, 9.5, '7. POST video data', 'right'),
        (5.5, 9, 9, '8. broadcast video to Client B', 'right'),
        (1.5, 7.5, 8.5, '9. POST audio data', 'right'),
        (7.5, 9, 8, '10. broadcast audio to Client B', 'right'),
        (9, 3.5, 7.5, '11. POST text message', 'left'),
        (3.5, 1.5, 7, '12. multicast text to Client A', 'left'),
        (1.5, 3.5, 6.5, '13. DISCONNECT', 'right'),
        (3.5, 9, 6, '14. broadcast RM to Client B', 'right'),
    ]
    
    # Draw messages
    for x1, x2, y, text, direction in messages:
        if direction == 'right':
            arrow = ConnectionPatch((x1, y), (x2, y), "data", "data",
                                  arrowstyle="->", shrinkA=2, shrinkB=2,
                                  mutation_scale=15, fc="blue", alpha=0.8)
        else:
            arrow = ConnectionPatch((x1, y), (x2, y), "data", "data",
                                  arrowstyle="<-", shrinkA=2, shrinkB=2,
                                  mutation_scale=15, fc="red", alpha=0.8)
        ax.add_patch(arrow)
        
        # Message text
        mid_x = (x1 + x2) / 2
        ax.text(mid_x, y + 0.2, text, ha='center', va='bottom', fontsize=8,
                bbox=dict(boxstyle="round,pad=0.2", facecolor='white', alpha=0.8))
    
    # Add activation boxes
    activations = [
        (3.5, 12.5, 6),    # Main server active
        (5.5, 11, 8.5),    # Video server active
        (7.5, 10.5, 8),    # Audio server active
    ]
    
    for x, start_y, end_y in activations:
        activation_box = FancyBboxPatch((x-0.05, end_y), 0.1, start_y-end_y, 
                                       boxstyle="square,pad=0", 
                                       facecolor='yellow', 
                                       alpha=0.5)
        ax.add_patch(activation_box)
    
    ax.set_xticks([])
    ax.set_yticks([])
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_visible(False)
    ax.spines['left'].set_visible(False)
    
    plt.tight_layout()
    plt.savefig('video_conference_sequence.png', dpi=300, bbox_inches='tight')
    plt.show()

if __name__ == "__main__":
    print("Generating workflow diagrams...")
    create_workflow_diagram()
    create_sequence_diagram()
    print("Diagrams saved as 'video_conference_workflow.png' and 'video_conference_sequence.png'")