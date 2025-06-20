import csv
import matplotlib.pyplot as plt

plt.style.use('dark_background')

def plot_graphs():
    try:
        with open('data.csv', 'r') as csvfile:
            reader = csv.reader(csvfile)
            next(reader)
    
            mois, ipc, annees, inflation = [], [], [], []
            for row in reader:
                mois.append(int(row[0]))
                ipc.append(float(row[1]))
                if row[3]:
                    annees.append(int(row[2]))
                    inflation.append(float(row[3]))

            fig = plt.figure(figsize=(14, 6))
            
        
            ax1 = plt.subplot(121)  
            ax2 = plt.subplot(122)  
            
            # Graphique IPC
            ax1.plot(mois, ipc, color='green', linewidth=2)
            ax1.set_title('Évolution de l\'IPC', pad=20)
            ax1.set_xlabel('Mois')
            ax1.set_ylabel('IPC')
            ax1.grid(True, linestyle='--', alpha=0.3)
            
            # Graphique Inflation
            if annees and inflation:
                annee_unique = sorted(list(set(annees)))
                ax2.plot(annee_unique, inflation, 'o-', color='red', linewidth=2)
                ax2.set_title('Inflation annuelle', pad=20)
                ax2.set_xlabel('Année')
                ax2.set_ylabel('Inflation (%)')
                ax2.set_xticks(annee_unique)
                ax2.grid(True, linestyle='--', alpha=0.3)
            
            # Ajustements finaux
            plt.tight_layout(pad=3.0)
            fig.subplots_adjust(wspace=0.3)
            
        
            manager = plt.get_current_fig_manager()
            try:
                manager.window.resize(800, 600)
            except AttributeError:
                try:
                    manager.resize(800, 600)
                except:
                    pass
            
            # Gestion de la fermeture
            fig.canvas.mpl_connect('key_press_event', 
                                lambda event: plt.close(fig) if event.key == 'escape' else None)
            
            plt.show()

    except Exception as e:
        print("pas de data.csv")

if __name__ == "__main__":
    plot_graphs()
