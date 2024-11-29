# Tratamiento de datos
# -----------------------------------------------------------------------
import numpy as np
import pandas as pd

# Otros objetivos
# -----------------------------------------------------------------------
import math

# Gráficos
# -----------------------------------------------------------------------
import seaborn as sns
import matplotlib.pyplot as plt

from scipy.stats import chi2_contingency
# Para tratar el problema de desbalance
# -----------------------------------------------------------------------
from imblearn.over_sampling import RandomOverSampler, SMOTE, SMOTENC
from imblearn.under_sampling import RandomUnderSampler, TomekLinks
from imblearn.combine import SMOTETomek

import os
import sys 

import warnings
warnings.filterwarnings("ignore")
sys.path.append(os.path.abspath("src"))   
import Soporte_preprocesamiento as f

# -----------------------------------------------------------------------
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix ,roc_auc_score, cohen_kappa_score


#EDA

def exploracion_dataframe(dataframe, columna_control, estadisticos = False):
    """
    Realiza un análisis exploratorio básico de un DataFrame, mostrando información sobre duplicados,
    valores nulos, tipos de datos, valores únicos para columnas categóricas y estadísticas descriptivas
    para columnas categóricas y numéricas, agrupadas por la columna de control.

    Params:
    - dataframe (DataFrame): El DataFrame que se va a explorar.
    - columna_control (str): El nombre de la columna que se utilizará como control para dividir el DataFrame.

    Returns: 
    No devuelve nada directamente, pero imprime en la consola la información exploratoria.
    """
    print(f"El número de datos es {dataframe.shape[0]} y el de columnas es {dataframe.shape[1]}")
    print("\n ..................... \n")

    print(f"Los duplicados que tenemos en el conjunto de datos son: {dataframe.duplicated().sum()}")
    print("\n ..................... \n")
    
    
    # generamos un DataFrame para los valores nulos
    print("Los nulos que tenemos en el conjunto de datos son:")
    df_nulos = pd.DataFrame(dataframe.isnull().sum() / dataframe.shape[0] * 100, columns = ["%_nulos"])
    display(df_nulos[df_nulos["%_nulos"] > 0])
    
    # Tipos de columnas
    print("\n ..................... \n")
    print(f"Los tipos de las columnas son:")
    display(pd.DataFrame(dataframe.dtypes, columns = ["tipo_dato"]))
    
    # Enseñar solo las columnas categoricas (o tipo objeto)
    print("\n ..................... \n")
    print("Los valores que tenemos para las columnas categóricas son: ")
    dataframe_categoricas = dataframe.select_dtypes(include = "O")
    
    for col in dataframe_categoricas.columns:
        print(f"La columna {col.upper()} tiene los siguientes valores únicos:")
        print(f"Mostrando {pd.DataFrame(dataframe[col].value_counts()).head().shape[0]} categorías con más valores del total de {len(pd.DataFrame(dataframe[col].value_counts()))} categorías ({pd.DataFrame(dataframe[col].value_counts()).head().shape[0]}/{len(pd.DataFrame(dataframe[col].value_counts()))})")
        display(pd.DataFrame(dataframe[col].value_counts()).head())    
    
    # como estamos en un problema de A/B testing y lo que realmente nos importa es comparar entre el grupo de control y el de test, los principales estadísticos los vamos a sacar de cada una de las categorías
    if estadisticos == True:
        for categoria in dataframe[columna_control].unique():
            dataframe_filtrado = dataframe[dataframe[columna_control] == categoria]
            #Describe de objetos
            print("\n ..................... \n")

            print(f"Los principales estadísticos de las columnas categóricas para el {categoria.upper()} son: ")
            display(dataframe_filtrado.describe(include = "O").T)

            #Hacer un describe
            print("\n ..................... \n")
            print(f"Los principales estadísticos de las columnas numéricas para el {categoria.upper()} son: ")
            display(dataframe_filtrado.describe().T)
    else: 
        pass
    print("\n----------\n")
    print("Las principales estadísticas de las variables númericas son:")
    display(dataframe.describe().T)

    print("\n----------\n")
    print("Las principales estadísticas de las variables categóricas son:")
    display(dataframe.describe(include = "O").T)

    print("\n----------\n")
    print("Las características principales del dataframe son:")
    display(dataframe.info())

def convertir_a_cat(lista_cols_convertir,df):
    for col in lista_cols_convertir:
        df[col]=df[col].astype("category")
        
    return df    

class Visualizador:
    """
    Clase para visualizar la distribución de variables numéricas y categóricas de un DataFrame.

    Attributes:
    - dataframe (pandas.DataFrame): El DataFrame que contiene las variables a visualizar.

    Methods:
    - __init__: Inicializa el VisualizadorDistribucion con un DataFrame y un color opcional para las gráficas.
    - separar_dataframes: Separa el DataFrame en dos subconjuntos, uno para variables numéricas y otro para variables categóricas.
    - plot_numericas: Grafica la distribución de las variables numéricas del DataFrame.
    - plot_categoricas: Grafica la distribución de las variables categóricas del DataFrame.
    - plot_relacion2: Visualiza la relación entre una variable y todas las demás, incluyendo variables numéricas y categóricas.
    """

    def __init__(self, dataframe):
        """
        Inicializa el VisualizadorDistribucion con un DataFrame y un color opcional para las gráficas.

        Parameters:
        - dataframe (pandas.DataFrame): El DataFrame que contiene las variables a visualizar.
        - color (str, opcional): El color a utilizar en las gráficas. Por defecto es "grey".
        """
        self.dataframe = dataframe

    def separar_dataframes(self):
        """
        Separa el DataFrame en dos subconjuntos, uno para variables numéricas y otro para variables categóricas.

        Returns:
        - pandas.DataFrame: DataFrame con variables numéricas.
        - pandas.DataFrame: DataFrame con variables categóricas.
        """
        return self.dataframe.select_dtypes(include=np.number), self.dataframe.select_dtypes(include=["O", "category"])
    
    def plot_numericas(self, color="grey", tamano_grafica=(20, 10)):
        """
        Grafica la distribución de las variables numéricas del DataFrame.

        Parameters:
        - color (str, opcional): El color a utilizar en las gráficas. Por defecto es "grey".
        - tamaño_grafica (tuple, opcional): El tamaño de la figura de la gráfica. Por defecto es (15, 5).
        """
        lista_num = self.separar_dataframes()[0].columns
        fig, axes = plt.subplots(ncols = 2, nrows = math.ceil(len(lista_num)/2), figsize=tamano_grafica, sharey=True)
        axes = axes.flat
        for indice, columna in enumerate(lista_num):
            sns.histplot(x=columna, data=self.dataframe, ax=axes[indice], color=color, bins=20)
            axes[indice].set_title(f"Distribución de {columna}")
        plt.suptitle("Distribución de variables numéricas")
        plt.tight_layout()

        if len(lista_num) % 2 !=0:
            fig.delaxes(axes[-1])


    def plot_categoricas(self, color="grey", tamano_grafica=(20, 10)):
        """
        Grafica la distribución de las variables categóricas del DataFrame.

        Parameters:
        - color (str, opcional): El color a utilizar en las gráficas. Por defecto es "grey".
        - tamaño_grafica (tuple, opcional): El tamaño de la figura de la gráfica. Por defecto es (15, 5).
        """
        lista_cat = self.separar_dataframes()[1].columns
        fig, axes = plt.subplots(ncols = 2, nrows = math.ceil(len(lista_cat) / 2), figsize=tamano_grafica)
        axes = axes.flat
        for indice, columna in enumerate(lista_cat):
            sns.countplot(x=columna, data=self.dataframe, order=self.dataframe[columna].value_counts().index,
                          ax=axes[indice], color=color)
            axes[indice].tick_params(rotation=90)
            axes[indice].set_title(columna)
            axes[indice].set(xlabel=None)

        plt.suptitle("Distribución de variables categóricas")
        plt.tight_layout()

        if len(lista_cat) % 2 !=0:
            fig.delaxes(axes[-1])


    def plot_relacion(self, vr, tamano_grafica=(20, 10), tamanio_fuente=18):


        lista_num = self.separar_dataframes()[0].columns
        lista_cat = self.separar_dataframes()[1].columns

        fig, axes = plt.subplots(ncols = 2, nrows = math.ceil(len(self.dataframe.columns) / 2), figsize=tamano_grafica)
        axes = axes.flat

        for indice, columna in enumerate(self.dataframe.columns):
            if columna == vr:
                fig.delaxes(axes[indice])
            elif columna in lista_num:
                sns.histplot(x = columna, 
                             hue = vr, 
                             data = self.dataframe, 
                             ax = axes[indice], 
                             palette = "magma", 
                             legend = False)
                
            elif columna in lista_cat:
                sns.countplot(x = columna, 
                              hue = vr, 
                              data = self.dataframe, 
                              ax = axes[indice], 
                              palette = "magma"
                              )

            axes[indice].set_title(f"Relación {columna} vs {vr}",size=tamanio_fuente)   

        plt.tight_layout()
    
        
    def deteccion_outliers(self, color = "grey"):

        """
        Detecta y visualiza valores atípicos en un DataFrame.

        Params:
            - dataframe (pandas.DataFrame):  El DataFrame que se va a usar

        Returns:
            No devuelve nada

        Esta función selecciona las columnas numéricas del DataFrame dado y crea un diagrama de caja para cada una de ellas para visualizar los valores atípicos.
        """

        lista_num = self.separar_dataframes()[0].columns

        fig, axes = plt.subplots(ncols = 2, nrows = math.ceil(len(lista_num)/2), figsize=(20,10))
        axes = axes.flat

        for indice, columna in enumerate(lista_num):
            sns.boxplot(x=columna, data=self.dataframe, 
                        ax=axes[indice], 
                        color=color, 
                        flierprops={'markersize': 4, 'markerfacecolor': 'orange'})
            axes[indice].set_title(f"Outliers {columna}")  

        if len(lista_num) % 2 != 0:
            fig.delaxes(axes[-1])

        
        plt.tight_layout()

    def correlacion(self, tamano_grafica = (7, 5)):

        """
        Visualiza la matriz de correlación de un DataFrame utilizando un mapa de calor.

        Params:
            - dataframe : pandas DataFrame. El DataFrame que contiene los datos para calcular la correlación.

        Returns:
        No devuelve nada 

        Muestra un mapa de calor de la matriz de correlación.

        - Utiliza la función `heatmap` de Seaborn para visualizar la matriz de correlación.
        - La matriz de correlación se calcula solo para las variables numéricas del DataFrame.
        - La mitad inferior del mapa de calor está oculta para una mejor visualización.
        - Permite guardar la imagen del mapa de calor como un archivo .png si se solicita.

        """

        plt.figure(figsize = tamano_grafica )

        mask = np.triu(np.ones_like(self.dataframe.corr(numeric_only=True), dtype = np.bool_))

        sns.heatmap(data = self.dataframe.corr(numeric_only = True), 
                    annot = True, 
                    vmin=-1,
                    vmax=1,
                    cmap="magma",
                    linecolor="black", 
                    fmt='.1g', 
                    mask = mask)
        
#ORDEN (ENCODING)

def detectar_orden_cat(df,lista_cat,var_respuesta):
    for categoria in lista_cat:
        print(f"Estamos evaluando el orden de la variable {categoria.upper()}")
        df_cross_tab=pd.crosstab(df[categoria], df[var_respuesta])
        display(df_cross_tab)
        
        chi2, p, dof, expected= chi2_contingency(df_cross_tab)

        if p <0.05:
            print(f"La variable {categoria} SI tiene orden")
        else:
            print(f"La variable {categoria} NO tiene orden")

#PLOT DE OUTLIERS (ESTANDARIZACION)

def visualizar_outliers_box(df, columnas_num):
    fig , axes = plt.subplots(nrows=8, ncols=5, figsize = (15, 20) )
    axes=axes.flat
    for index,col in enumerate(columnas_num,start=0):

        sns.boxplot(x = col, data = df, ax = axes[index])
        
        
    plt.tight_layout()


## OUTLIERS

def identificar_outliers_iqr(df, k=1.5):
    df_num=df.select_dtypes(include=np.number)
    dicc_outliers={}
    for columna in df_num.columns:
        Q1, Q3= np.nanpercentile(df[columna], (25, 75))
        iqr= Q3 - Q1
        limite_superior= Q3 + (iqr * k)
        limite_inferior= Q1 - (iqr * k)

        condicion_sup= df[columna] > limite_superior
        condicion_inf= df[columna] < limite_inferior
        df_outliers= df[condicion_inf | condicion_sup]
        print(f"La columna {columna.upper()} tiene {df_outliers.shape[0]} outliers")
        if not df_outliers.empty:
            dicc_outliers[columna]= df_outliers

    return dicc_outliers    


#DESBALANCES

class Desbalanceo:
    def __init__(self, dataframe, variable_dependiente):
        self.dataframe = dataframe
        self.variable_dependiente = variable_dependiente

    def visualizar_clase(self, color="orange", edgecolor="black"):
        plt.figure(figsize=(8, 5))  # para cambiar el tamaño de la figura
        fig = sns.countplot(data=self.dataframe, 
                            x=self.variable_dependiente,  
                            color=color,  
                            edgecolor=edgecolor)
        fig.set(xticklabels=["No", "Yes"])
        plt.show()

    def balancear_clases_pandas(self, metodo):

        # Contar las muestras por clase
        contar_clases = self.dataframe[self.variable_dependiente].value_counts()
        clase_mayoritaria = contar_clases.idxmax()
        clase_minoritaria = contar_clases.idxmin()

        # Separar las clases
        df_mayoritaria = self.dataframe[self.dataframe[self.variable_dependiente] == clase_mayoritaria]
        df_minoritaria = self.dataframe[self.dataframe[self.variable_dependiente] == clase_minoritaria]

        if metodo == "downsampling":
            # Submuestrear la clase mayoritaria
            df_majority_downsampled = df_mayoritaria.sample(contar_clases[clase_minoritaria], random_state=42)
            # Combinar los subconjuntos
            df_balanced = pd.concat([df_majority_downsampled, df_minoritaria])

        elif metodo == "upsampling":
            # Sobremuestrear la clase minoritaria
            df_minority_upsampled = df_minoritaria.sample(contar_clases[clase_mayoritaria], replace=True, random_state=42)
            # Combinar los subconjuntos
            df_balanced = pd.concat([df_mayoritaria, df_minority_upsampled])

        else:
            raise ValueError("Método no reconocido. Use 'downsampling' o 'upsampling'.")

        return df_balanced

    def balancear_clases_imblearn(self, metodo):

        X = self.dataframe.drop(columns=[self.variable_dependiente])
        y = self.dataframe[self.variable_dependiente]

        if metodo == "RandomOverSampler":
            ros = RandomOverSampler(random_state=42)
            X_resampled, y_resampled = ros.fit_resample(X, y)

        elif metodo == "RandomUnderSampler":
            rus = RandomUnderSampler(random_state=42)
            X_resampled, y_resampled = rus.fit_resample(X, y)

        else:
            raise ValueError("Método no reconocido. Use 'RandomOverSampler' o 'RandomUnderSampler'.")

        df_resampled = pd.concat([pd.DataFrame(X_resampled), pd.Series(y_resampled, name=self.variable_dependiente)], axis=1)
        return df_resampled
    
    def balancear_clases_smote(self):
        X = self.dataframe.drop(columns=[self.variable_dependiente])
        y = self.dataframe[self.variable_dependiente]

        smote = SMOTE(random_state=42)
        X_resampled, y_resampled = smote.fit_resample(X, y)
        
        df_resampled = pd.concat([pd.DataFrame(X_resampled, columns=X.columns), pd.Series(y_resampled, name=self.variable_dependiente)], axis=1)
        return df_resampled

    def balancear_clase_smotenc(self, columnas_categoricas__encoded):
        X = self.dataframe.drop(columns=[self.variable_dependiente])
        y = self.dataframe[self.variable_dependiente]

        smotenc = SMOTENC(random_state=42, categorical_features=columnas_categoricas__encoded)
        X_resampled, y_resampled = smote.fit_resample(X, y)
        
        df_resampled = pd.concat([pd.DataFrame(X_resampled, columns=X.columns), pd.Series(y_resampled, name=self.variable_dependiente)], axis=1)
        return df_resampled


    def balancear_clases_smote_tomek(self):
        X = self.dataframe.drop(columns=[self.variable_dependiente])
        y = self.dataframe[self.variable_dependiente]

        smote_tomek = SMOTETomek(random_state=42)
        X_resampled, y_resampled = smote_tomek.fit_resample(X, y)
        
        df_resampled = pd.concat([pd.DataFrame(X_resampled, columns=X.columns), pd.Series(y_resampled, name=self.variable_dependiente)], axis=1)
        return df_resampled


## CALCULAR MÉTRICAS DE CLASIFICACIÓN

def calcular_metricas(y_train, y_test, pred_train, pred_test, prob_test, prob_train):
    """
    Calcula métricas de rendimiento para el modelo seleccionado.
    """
    
    # Métricas
    metricas_train = {
        "accuracy": accuracy_score(y_train, pred_train),
        "precision": precision_score(y_train, pred_train, average='weighted', zero_division=0),
        "recall": recall_score(y_train, pred_train, average='weighted', zero_division=0),
        "f1": f1_score(y_train, pred_train, average='weighted', zero_division=0),
        "kappa": cohen_kappa_score(y_train, pred_train),
        "auc": roc_auc_score(y_train, prob_train) if prob_train is not None else None 

    }
    metricas_test = {
        "accuracy": accuracy_score(y_test, pred_test),
        "precision": precision_score(y_test, pred_test, average='weighted', zero_division=0),
        "recall": recall_score(y_test, pred_test, average='weighted', zero_division=0),
        "f1": f1_score(y_test, pred_test, average='weighted', zero_division=0),
        "kappa": cohen_kappa_score(y_test, pred_test),
        "auc": roc_auc_score(y_test, prob_test) if prob_test is not None else None
    }

    return pd.DataFrame({"train": metricas_train, "test": metricas_test})
        

def plot_matriz_confusion(matriz_confusion, invertir=True, tamano_grafica=(4, 3), labels=False, label0="", label1="", color="Purples"):
    """
    Genera un heatmap para visualizar una matriz de confusión.

    Args:
        matriz_confusion (numpy.ndarray): Matriz de confusión que se desea graficar.
        invertir (bool, opcional): Si es True, invierte el orden de las filas y columnas de la matriz
            para reflejar el eje Y invertido (orden [1, 0] en lugar de [0, 1]). Por defecto, True.
        tamano_grafica (tuple, opcional): Tamaño de la figura en pulgadas. Por defecto, (4, 3).
        labels (bool, opcional): Si es True, permite agregar etiquetas personalizadas a las clases
            utilizando `label0` y `label1`. Por defecto, False.
        label0 (str, opcional): Etiqueta personalizada para la clase 0 (negativa). Por defecto, "".
        label1 (str, opcional): Etiqueta personalizada para la clase 1 (positiva). Por defecto, "".

    Returns:
        None: La función no retorna ningún valor, pero muestra un heatmap con la matriz de confusión.

    Ejemplos:
>             from sklearn.metrics import confusion_matrix
>         >>> y_true = [0, 1, 1, 0, 1, 1]
>         >>> y_pred = [0, 1, 1, 0, 0, 1]
>         >>> matriz_confusion = confusion_matrix(y_true, y_pred)
>         >>> plot_matriz_confusion(matriz_confusion, invertir=True, labels=True, label0="Clase Negativa", label1="Clase Positiva")
    """
    if invertir == True:
        plt.figure(figsize=(tamano_grafica))
        if labels == True:
            labels = [f'1: {label1}', f'0: {label0}']
        else:
            labels = [f'1', f'0']
        sns.heatmap(matriz_confusion[::-1, ::-1], annot=True, fmt="d", xticklabels=labels, yticklabels=labels, cmap= color)
        plt.xlabel("Predicción")
        plt.ylabel("Real");
    else: 
        plt.figure(figsize=(tamano_grafica))
        if labels == True:
            labels = [f'0: {label0}', f'1: {label1}']
        else:
            labels = [f'0', f'1']
        sns.heatmap(matriz_confusion, annot=True, fmt="d", xticklabels=labels, yticklabels=labels, cmap= color)    
        plt.xlabel("Predicción")
        plt.ylabel("Real");  
